"""
Use case: re-verify every PENDING/FAILED purchase against the payment
provider and finalize it.

Ported from :py:func:`app.commands.synchronise.synchronize_transactions`. Key
design move: this use case **delegates each purchase to**
:class:`ConfirmPayment` instead of duplicating the verify + amount-check +
delivery logic. That removes the entire class of bugs we hit in cd1d2cc
(legacy sync had drifted from the callback and let amount-mismatches slip
through). One source of truth, two callers (HTTP callback + CLI sync).

Skip conditions:

- the purchase has no provider ``transactionId`` yet (column empty AND no
  metadata fallback) — the legacy code did the same; for Kkiapay we can't
  verify without it, and the internal uuid is never a valid Kkiapay handle;
- already in ``SUCCESS`` — list_pending already filters these out, but the
  guard is cheap and keeps the use case safe to call with a hand-crafted
  list.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.application.ports import PurchaseRepositoryPort
from src.application.use_cases.confirm_payment import (
    ConfirmPayment,
    ConfirmPaymentInput,
    PurchaseNotFound,
)
from src.domain import PurchaseStatus

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ReconcilePendingInput:
    book_ids: list[str] | None = None  # None = no product filter


@dataclass(slots=True)
class ReconcileSummary:
    """Mutable accumulator returned at the end of one run."""

    processed: int = 0
    confirmed: int = 0
    failed: int = 0
    skipped: int = 0
    errored: int = 0
    purchase_ids_confirmed: list[str] = field(default_factory=list)


def _resolve_provider_tx_id(purchase) -> str | None:
    """Kkiapay-style resolution: column first, metadata fallback for legacy
    rows. Never falls back to the internal uuid (Kkiapay would just refuse)."""
    if purchase.payment_ref.provider_tx_id:
        return purchase.payment_ref.provider_tx_id
    fallback = purchase.payment_metadata.get("transactionId")
    return fallback if isinstance(fallback, str) and fallback else None


class ReconcilePending:
    def __init__(self, purchases: PurchaseRepositoryPort, confirm: ConfirmPayment) -> None:
        self._purchases = purchases
        self._confirm = confirm

    async def execute(self, cmd: ReconcilePendingInput) -> ReconcileSummary:
        purchases = await self._purchases.list_pending(cmd.book_ids)
        summary = ReconcileSummary()
        if not purchases:
            log.info("Reconcile: nothing to do (book_ids=%s)", cmd.book_ids)
            return summary

        log.info("Reconcile: %d purchase(s) to inspect", len(purchases))
        for purchase in purchases:
            summary.processed += 1
            if purchase.status is PurchaseStatus.SUCCESS:
                continue
            provider_tx_id = _resolve_provider_tx_id(purchase)
            if not provider_tx_id:
                log.warning("Missing provider transactionId for %s, skipping", purchase.id)
                summary.skipped += 1
                continue
            try:
                result = await self._confirm.execute(
                    ConfirmPaymentInput(purchase_id=purchase.id, provider_tx_id=provider_tx_id)
                )
            except PurchaseNotFound:
                # Vanishingly rare race (row deleted between query and confirm);
                # treat as skipped.
                summary.skipped += 1
                continue
            except Exception:
                log.exception("Reconcile errored on %s", purchase.id)
                summary.errored += 1
                continue
            if result.confirmed:
                summary.confirmed += 1
                summary.purchase_ids_confirmed.append(purchase.id)
            else:
                summary.failed += 1
        log.info(
            "Reconcile complete: processed=%d confirmed=%d failed=%d skipped=%d errored=%d",
            summary.processed,
            summary.confirmed,
            summary.failed,
            summary.skipped,
            summary.errored,
        )
        return summary
