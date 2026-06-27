"""
Unit tests for :class:`ReconcilePending`. Uses a spy ConfirmPayment so we can
assert on the delegation pattern without re-testing ConfirmPayment's own
guards (those are covered by ``test_confirm_payment.py``).
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.application.use_cases import (
    ConfirmPaymentInput,
    ConfirmPaymentOutput,
    PurchaseNotFound,
    ReconcilePending,
    ReconcilePendingInput,
)
from src.domain import (
    Currency,
    Customer,
    Money,
    PaymentProviderName,
    PaymentReference,
    Purchase,
    PurchaseStatus,
)


class FakeRepo:
    def __init__(self, pending: list[Purchase]) -> None:
        self.pending = list(pending)
        self.list_pending_calls: list[list[str] | None] = []

    async def add(self, p):
        self.pending.append(p)

    async def get(self, pid):
        return next((p for p in self.pending if p.id == pid), None)

    async def get_by_provider_tx_id(self, ptid):
        return None

    async def save(self, p):
        pass

    async def list_pending(self, book_ids: list[str] | None = None) -> list[Purchase]:
        self.list_pending_calls.append(book_ids)
        if book_ids is None:
            return list(self.pending)
        return [p for p in self.pending if p.book_id in book_ids]


@dataclass
class ConfirmSpy:
    """Stand-in for ConfirmPayment that records calls and returns a scripted outcome."""

    outcomes: dict[str, bool]  # purchase_id -> confirmed
    calls: list[ConfirmPaymentInput]

    def __init__(self, outcomes: dict[str, bool] | None = None, missing: set[str] | None = None) -> None:
        self.outcomes = outcomes or {}
        self.missing = missing or set()
        self.calls = []

    async def execute(self, cmd: ConfirmPaymentInput) -> ConfirmPaymentOutput:
        self.calls.append(cmd)
        if cmd.purchase_id in self.missing:
            raise PurchaseNotFound(cmd.purchase_id)
        confirmed = self.outcomes.get(cmd.purchase_id, False)
        # We don't need a real Purchase to satisfy the type contract of the
        # output for these tests — ReconcilePending only reads `confirmed`.
        return ConfirmPaymentOutput(purchase=None, confirmed=confirmed, delivered=False)  # type: ignore[arg-type]


def _purchase(
    *,
    id_: str,
    book_id: str = "lutte-contre-fraude",
    provider_tx_id: str | None = None,
    status: PurchaseStatus = PurchaseStatus.PENDING,
    metadata_tx_id: str | None = None,
) -> Purchase:
    p = Purchase(
        id=id_,
        book_id=book_id,
        customer=Customer(email="x@y.z", name="X", phone="+225", country="CI", city="Abidjan"),
        amount=Money(amount=20_000, currency=Currency.XOF),
        status=status,
        payment_ref=PaymentReference(provider=PaymentProviderName.KKIAPAY, provider_tx_id=provider_tx_id),
    )
    if metadata_tx_id:
        p = p.merge_payment_metadata(transactionId=metadata_tx_id)
    return p


@pytest.mark.asyncio
async def test_summary_counts_confirmed_failed_skipped_errored():
    pending = [
        _purchase(id_="A", provider_tx_id="kkia_A"),  # will confirm
        _purchase(id_="B", provider_tx_id="kkia_B"),  # will fail
        _purchase(id_="C", provider_tx_id=None),  # skipped (no id)
        _purchase(id_="D", provider_tx_id="kkia_D"),  # errors
    ]
    confirm = ConfirmSpy(outcomes={"A": True, "B": False, "D": False})
    repo = FakeRepo(pending)

    async def explode(cmd):
        if cmd.purchase_id == "D":
            raise RuntimeError("provider down")
        confirm.calls.append(cmd)
        return ConfirmPaymentOutput(purchase=None, confirmed=cmd.purchase_id == "A", delivered=False)  # type: ignore[arg-type]

    confirm.execute = explode  # type: ignore[assignment]

    use_case = ReconcilePending(purchases=repo, confirm=confirm)  # type: ignore[arg-type]
    summary = await use_case.execute(ReconcilePendingInput())

    assert summary.processed == 4
    assert summary.confirmed == 1
    assert summary.failed == 1
    assert summary.skipped == 1
    assert summary.errored == 1
    assert summary.purchase_ids_confirmed == ["A"]


@pytest.mark.asyncio
async def test_book_id_filter_is_passed_to_repository():
    repo = FakeRepo([])
    use_case = ReconcilePending(purchases=repo, confirm=ConfirmSpy())  # type: ignore[arg-type]
    await use_case.execute(ReconcilePendingInput(book_ids=["lutte-contre-fraude"]))
    assert repo.list_pending_calls == [["lutte-contre-fraude"]]


@pytest.mark.asyncio
async def test_metadata_transactionid_is_used_as_fallback_for_provider_id():
    """Legacy rows may carry the Kkiapay id only in payment_metadata."""
    p = _purchase(id_="legacy", provider_tx_id=None, metadata_tx_id="kkia_legacy")
    confirm = ConfirmSpy(outcomes={"legacy": True})
    use_case = ReconcilePending(purchases=FakeRepo([p]), confirm=confirm)  # type: ignore[arg-type]
    summary = await use_case.execute(ReconcilePendingInput())
    assert summary.confirmed == 1
    assert confirm.calls[0].provider_tx_id == "kkia_legacy"


@pytest.mark.asyncio
async def test_success_purchases_are_skipped_defensively():
    """List should not contain SUCCESS rows, but we double-guard."""
    p = _purchase(id_="done", provider_tx_id="kkia_x", status=PurchaseStatus.SUCCESS)
    confirm = ConfirmSpy()
    use_case = ReconcilePending(purchases=FakeRepo([p]), confirm=confirm)  # type: ignore[arg-type]
    summary = await use_case.execute(ReconcilePendingInput())
    assert summary.processed == 1
    assert summary.confirmed == 0
    assert confirm.calls == []
