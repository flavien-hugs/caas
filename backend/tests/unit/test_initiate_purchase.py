"""
Unit tests for :class:`InitiatePurchase`. No DB, no HTTP — fake adapters only.
"""

from __future__ import annotations

import pytest

from src.application.use_cases import (
    InitiatePurchase,
    InitiatePurchaseInput,
    ProviderInitiationFailed,
    UnknownProduct,
)
from src.domain import (
    Currency,
    Customer,
    DeliveryMethod,
    Money,
    PaymentProviderName,
    Product,
    Purchase,
    PurchaseStatus,
)


class FakePurchaseRepo:
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


class FakeProductRepo:
    def __init__(self, products: dict[str, Product]) -> None:
        self.products = products

    async def get(self, book_id: str) -> Product | None:
        return self.products.get(book_id)


class FakeProvider:
    def __init__(self, url: str = "/payment/render/x") -> None:
        self.url = url
        self.calls: list[str] = []

    async def initiate_payment(self, purchase: Purchase) -> str:
        self.calls.append(purchase.id)
        return self.url

    async def verify_payment(self, provider_tx_id: str) -> dict:
        return {"status": "PENDING"}


class FailingProvider:
    async def initiate_payment(self, purchase: Purchase) -> str:
        raise RuntimeError("boom")

    async def verify_payment(self, provider_tx_id: str) -> dict:
        return {"status": "PENDING"}


def _customer() -> Customer:
    return Customer(email="x@y.z", name="X Y", phone="+225 00 00", country="CI", city="Abidjan")


def _fraude_product() -> Product:
    return Product(
        book_id="lutte-contre-fraude",
        name="Webinaire",
        price=Money(amount=20_000, currency=Currency.XOF),
        delivery_method=DeliveryMethod.WHATSAPP,
        delivery_payload="https://chat.whatsapp.com/X",
    )


@pytest.fixture
def deps():
    purchases = FakePurchaseRepo()
    products = FakeProductRepo({"lutte-contre-fraude": _fraude_product()})
    provider = FakeProvider()
    use_case = InitiatePurchase(
        purchases=purchases,
        products=products,
        provider=provider,
        provider_name=PaymentProviderName.KKIAPAY,
    )
    return use_case, purchases, products, provider


@pytest.mark.asyncio
async def test_initiate_purchase_persists_pending_row_at_server_price(deps):
    use_case, purchases, _, provider = deps
    out = await use_case.execute(InitiatePurchaseInput(book_id="lutte-contre-fraude", customer=_customer(), client_amount=999))

    assert out.payment_url.startswith("/payment/render/")
    assert out.server_amount == Money(amount=20_000, currency=Currency.XOF)
    saved = purchases.store[out.purchase_id]
    assert saved.status is PurchaseStatus.PENDING
    # Server price wins even when client tampers
    assert saved.amount == Money(amount=20_000, currency=Currency.XOF)
    assert saved.payment_metadata.get("checkout_url") == provider.url


@pytest.mark.asyncio
async def test_initiate_purchase_raises_unknown_product(deps):
    use_case, _, _, _ = deps
    with pytest.raises(UnknownProduct):
        await use_case.execute(InitiatePurchaseInput(book_id="does-not-exist", customer=_customer()))


@pytest.mark.asyncio
async def test_initiate_purchase_flips_to_error_when_provider_fails():
    purchases = FakePurchaseRepo()
    use_case = InitiatePurchase(
        purchases=purchases,
        products=FakeProductRepo({"lutte-contre-fraude": _fraude_product()}),
        provider=FailingProvider(),
        provider_name=PaymentProviderName.KKIAPAY,
    )

    with pytest.raises(ProviderInitiationFailed):
        await use_case.execute(InitiatePurchaseInput(book_id="lutte-contre-fraude", customer=_customer()))

    # Row must still be findable in ERROR status — never lost.
    [saved] = list(purchases.store.values())
    assert saved.status is PurchaseStatus.ERROR
    assert saved.payment_metadata.get("initiation_error") == "boom"
