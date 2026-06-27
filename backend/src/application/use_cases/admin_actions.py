"""
Admin actions: re-send a delivery, manually confirm a payment by attaching a
provider transactionId, export the filtered transactions to Excel.

Critical invariant for ``AdminConfirmPayment``: it MUST go through
:class:`ConfirmPayment` so the amount-mismatch / security_error guard
applies. The legacy ``/sync-payment/{tx_id}`` endpoint shipped without
that check — vulnerability #3 of the security review — and we will not
reproduce the gap.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from io import BytesIO

import xlsxwriter

from src.application.dashboard_filters import TransactionFilters
from src.application.ports import NotificationPort, PurchaseRepositoryPort
from src.application.use_cases.confirm_payment import (
    ConfirmPayment,
    ConfirmPaymentInput,
    ConfirmPaymentOutput,
    PurchaseNotFound,
)
from src.domain import Purchase, PurchaseStatus

# --- Resend delivery ---------------------------------------------------------


class PurchaseNotEligibleForResend(Exception):
    """Raised when the admin tries to re-deliver a non-SUCCESS purchase."""


@dataclass(frozen=True, slots=True)
class ResendDeliveryInput:
    purchase_id: str


class ResendDelivery:
    """Force a re-delivery (email / WhatsApp link reminder / …) for a
    SUCCESS purchase. Does not flip ``email_sent`` — admin re-sends are
    explicit operator actions, idempotency lives in the regular pipeline."""

    def __init__(self, purchases: PurchaseRepositoryPort, notification: NotificationPort) -> None:
        self._purchases = purchases
        self._notification = notification

    async def execute(self, cmd: ResendDeliveryInput) -> Purchase:
        purchase = await self._purchases.get(cmd.purchase_id)
        if purchase is None:
            raise PurchaseNotFound(cmd.purchase_id)
        if purchase.status is not PurchaseStatus.SUCCESS:
            raise PurchaseNotEligibleForResend(
                f"purchase {cmd.purchase_id} is in {purchase.status.value}, delivery can only be resent for SUCCESS purchases"
            )
        await self._notification.deliver(purchase)
        return purchase


# --- Admin sync (manual confirm) ---------------------------------------------


class ProviderTxIdAlreadyLinked(Exception):
    """The provider tx id is already attached to a different purchase."""


@dataclass(frozen=True, slots=True)
class AdminConfirmPaymentInput:
    purchase_id: str
    provider_tx_id: str


class AdminConfirmPayment:
    """Operator-driven path of the regular confirm flow. The actual
    verify + amount-check + delivery is delegated to :class:`ConfirmPayment`
    so the security guards apply uniformly."""

    def __init__(self, purchases: PurchaseRepositoryPort, confirm: ConfirmPayment) -> None:
        self._purchases = purchases
        self._confirm = confirm

    async def execute(self, cmd: AdminConfirmPaymentInput) -> ConfirmPaymentOutput:
        # Refuse to attach a transactionId that already belongs to another row.
        existing = await self._purchases.get_by_provider_tx_id(cmd.provider_tx_id)
        if existing is not None and existing.id != cmd.purchase_id:
            raise ProviderTxIdAlreadyLinked(f"provider_tx_id={cmd.provider_tx_id!r} is already linked to {existing.id}")
        return await self._confirm.execute(ConfirmPaymentInput(purchase_id=cmd.purchase_id, provider_tx_id=cmd.provider_tx_id))


# --- Excel export ------------------------------------------------------------


class ExportTransactions:
    """Streams every matching row into an in-memory xlsx and returns the
    bytes. Designed for the admin's "Export Excel" button — generally
    small enough to hold in memory; if it ever grows we'll switch to a
    streaming writer with chunked HTTP."""

    COLUMNS = (
        ("ID", lambda p: p.id),
        ("Created at", lambda p: p.created_at.strftime("%Y-%m-%d %H:%M")),
        ("Book ID", lambda p: p.book_id),
        ("Status", lambda p: p.status.value),
        ("Amount", lambda p: p.amount.amount),
        ("Currency", lambda p: p.amount.currency.value),
        ("Provider TX ID", lambda p: p.payment_ref.provider_tx_id or ""),
        ("Email", lambda p: p.customer.email),
        ("Name", lambda p: p.customer.name),
        ("Phone", lambda p: p.customer.phone),
        ("Country", lambda p: p.customer.country),
        ("City", lambda p: p.customer.city),
    )

    def __init__(self, purchases: PurchaseRepositoryPort) -> None:
        self._purchases = purchases

    async def execute(self, filters: TransactionFilters) -> bytes:
        buf = BytesIO()
        workbook = xlsxwriter.Workbook(buf, {"in_memory": True})
        worksheet = workbook.add_worksheet("transactions")

        bold = workbook.add_format({"bold": True})
        for col, (header, _) in enumerate(self.COLUMNS):
            worksheet.write(0, col, header, bold)

        row_index = 1
        async for purchase in self._iter(filters):
            for col, (_, extract) in enumerate(self.COLUMNS):
                worksheet.write(row_index, col, extract(purchase))
            row_index += 1

        workbook.close()
        return buf.getvalue()

    async def _iter(self, filters: TransactionFilters) -> AsyncIterator[Purchase]:
        async for purchase in self._purchases.iter_for_export(filters):
            yield purchase
