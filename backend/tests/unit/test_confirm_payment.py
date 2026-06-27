"""
Unit tests for :class:`ConfirmPayment`. Fakes only.

Covers the security-critical branches inherited from
:py:func:`app.routers.payment.payment_callback`:

- ``security_error`` purchases must not be resurrected;
- amount mismatch (vs Purchase.amount) must flip to FAILED + security_error;
- a non-SUCCESS provider verdict must flip to FAILED without delivery;
- a SUCCESS verdict must persist SUCCESS, link transaction_id, and
  *not* deliver when ``DeliveryMethod`` is not EMAIL (fraude/WhatsApp);
- idempotency: re-running on a row with ``email_sent=True`` must not
  deliver again.
"""

from __future__ import annotations

import pytest

from src.application.use_cases import ConfirmPayment, ConfirmPaymentInput, PurchaseNotFound
from src.domain import (
    Currency,
    Customer,
    DeliveryMethod,
    Money,
    PaymentProviderName,
    PaymentReference,
    Product,
    Purchase,
    PurchaseStatus,
)


class FakeRepo:
    def __init__(self) -> None:
        self.store: dict[str, Purchase] = {}

    async def add(self, p: Purchase) -> None:
        self.store[p.id] = p

    async def get(self, purchase_id: str) -> Purchase | None:
        return self.store.get(purchase_id)

    async def get_by_provider_tx_id(self, provider_tx_id: str) -> Purchase | None:
        for p in self.store.values():
            if p.payment_ref.provider_tx_id == provider_tx_id:
                return p
        return None

    async def save(self, p: Purchase) -> None:
        self.store[p.id] = p

    async def list_pending(self, book_ids: list[str] | None = None) -> list[Purchase]:
        return [p for p in self.store.values() if p.status is PurchaseStatus.PENDING]


class FakeProducts:
    def __init__(self, by_id: dict[str, Product]) -> None:
        self.by_id = by_id

    async def get(self, book_id: str) -> Product | None:
        return self.by_id.get(book_id)


class FakeProvider:
    def __init__(self, result: dict) -> None:
        self.result = result

    async def initiate_payment(self, purchase: Purchase) -> str:  # not used
        return ""

    async def verify_payment(self, provider_tx_id: str) -> dict:
        return self.result


class SpyNotification:
    def __init__(self) -> None:
        self.deliveries: list[str] = []

    async def deliver(self, purchase: Purchase) -> None:
        self.deliveries.append(purchase.id)


def _purchase(book_id: str = "lutte-contre-fraude", amount: int = 20_000, **meta) -> Purchase:
    p = Purchase.new(
        book_id=book_id,
        customer=Customer(email="x@y.z", name="X Y", phone="+225", country="CI", city="Abidjan"),
        amount=Money(amount=amount, currency=Currency.XOF),
        payment_ref=PaymentReference(provider=PaymentProviderName.KKIAPAY),
    )
    if meta:
        p = p.merge_payment_metadata(**meta)
    return p


def _fraude(price: int = 20_000) -> Product:
    return Product(
        book_id="lutte-contre-fraude",
        name="Webinaire",
        price=Money(amount=price, currency=Currency.XOF),
        delivery_method=DeliveryMethod.WHATSAPP,
    )


def _email_product(price: int = 7_000) -> Product:
    return Product(
        book_id="multi-business",
        name="Pack PDF",
        price=Money(amount=price, currency=Currency.XOF),
        delivery_method=DeliveryMethod.EMAIL,
    )


@pytest.mark.asyncio
async def test_security_error_rows_are_not_resurrected():
    repo = FakeRepo()
    p = _purchase(security_error="amount_mismatch").with_status(PurchaseStatus.FAILED)
    await repo.add(p)
    use_case = ConfirmPayment(
        purchases=repo,
        products=FakeProducts({"lutte-contre-fraude": _fraude()}),
        provider=FakeProvider({"status": "SUCCESS", "amount": 20_000}),
        notification=SpyNotification(),
    )
    out = await use_case.execute(ConfirmPaymentInput(purchase_id=p.id, provider_tx_id="kkia_1"))
    assert out.confirmed is False
    # untouched
    assert repo.store[p.id].status is PurchaseStatus.FAILED
    assert repo.store[p.id].payment_metadata["security_error"] == "amount_mismatch"


@pytest.mark.asyncio
async def test_amount_mismatch_flips_to_failed_with_security_error():
    repo = FakeRepo()
    p = _purchase(amount=20_000)
    await repo.add(p)
    use_case = ConfirmPayment(
        purchases=repo,
        products=FakeProducts({"lutte-contre-fraude": _fraude()}),
        provider=FakeProvider({"status": "SUCCESS", "amount": 999}),
        notification=SpyNotification(),
    )
    out = await use_case.execute(ConfirmPaymentInput(purchase_id=p.id, provider_tx_id="kkia_1"))
    assert out.confirmed is False
    assert out.delivered is False
    saved = repo.store[p.id]
    assert saved.status is PurchaseStatus.FAILED
    assert saved.payment_metadata["security_error"] == "amount_mismatch"


@pytest.mark.asyncio
async def test_provider_failure_status_marks_failed_without_delivery():
    repo = FakeRepo()
    p = _purchase()
    await repo.add(p)
    spy = SpyNotification()
    use_case = ConfirmPayment(
        purchases=repo,
        products=FakeProducts({"lutte-contre-fraude": _fraude()}),
        provider=FakeProvider({"status": "FAILED"}),
        notification=spy,
    )
    out = await use_case.execute(ConfirmPaymentInput(purchase_id=p.id, provider_tx_id="kkia_1"))
    assert out.confirmed is False
    assert out.delivered is False
    assert spy.deliveries == []
    assert repo.store[p.id].status is PurchaseStatus.FAILED


@pytest.mark.asyncio
async def test_success_for_whatsapp_product_does_not_deliver():
    """Fraude/WhatsApp: confirm SUCCESS but no email is sent — page handles it."""
    repo = FakeRepo()
    p = _purchase()
    await repo.add(p)
    spy = SpyNotification()
    use_case = ConfirmPayment(
        purchases=repo,
        products=FakeProducts({"lutte-contre-fraude": _fraude()}),
        provider=FakeProvider({"status": "SUCCESS", "amount": 20_000}),
        notification=spy,
    )
    out = await use_case.execute(ConfirmPaymentInput(purchase_id=p.id, provider_tx_id="kkia_1"))
    assert out.confirmed is True
    assert out.delivered is False
    assert spy.deliveries == []
    saved = repo.store[p.id]
    assert saved.status is PurchaseStatus.SUCCESS
    assert saved.payment_ref.provider_tx_id == "kkia_1"


@pytest.mark.asyncio
async def test_success_for_email_product_delivers_once():
    repo = FakeRepo()
    p = _purchase(book_id="multi-business", amount=7_000)
    await repo.add(p)
    spy = SpyNotification()
    use_case = ConfirmPayment(
        purchases=repo,
        products=FakeProducts({"multi-business": _email_product()}),
        provider=FakeProvider({"status": "SUCCESS", "amount": 7_000}),
        notification=spy,
    )
    out = await use_case.execute(ConfirmPaymentInput(purchase_id=p.id, provider_tx_id="kkia_2"))
    assert out.confirmed is True
    assert out.delivered is True
    assert spy.deliveries == [p.id]
    assert repo.store[p.id].payment_metadata["email_sent"] is True

    # Re-run: idempotent, no second delivery.
    out2 = await use_case.execute(ConfirmPaymentInput(purchase_id=p.id, provider_tx_id="kkia_2"))
    assert out2.confirmed is True
    assert out2.delivered is False
    assert spy.deliveries == [p.id]  # unchanged


@pytest.mark.asyncio
async def test_unknown_purchase_raises():
    use_case = ConfirmPayment(
        purchases=FakeRepo(),
        products=FakeProducts({}),
        provider=FakeProvider({"status": "SUCCESS"}),
        notification=SpyNotification(),
    )
    with pytest.raises(PurchaseNotFound):
        await use_case.execute(ConfirmPaymentInput(purchase_id="missing", provider_tx_id="x"))
