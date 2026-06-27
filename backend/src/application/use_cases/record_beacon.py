"""
Use case: record the provider transactionId emitted by the widget via
``navigator.sendBeacon`` right before the success/failure redirect.

Job is intentionally minimal — durably link the provider id to the purchase
so the periodic reconciliation can still confirm the payment even if the
browser redirect to ``/payment/callback`` never completes. The financial
decision (status / amount validation) is *not* made here; see
:class:`ConfirmPayment`.

Ported from :py:func:`app.routers.payment.payment_beacon`. Same guards:

- ignore unknown ids (don't crash on stale or hostile inputs);
- never touch a purchase already in ``SUCCESS``;
- never overwrite an existing payment reference (that link belongs to
  the original payment session, not the beacon).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from src.application.ports import PurchaseRepositoryPort
from src.domain import PaymentReference, PurchaseStatus

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RecordBeaconInput:
    purchase_id: str
    provider_tx_id: str


class RecordBeacon:
    def __init__(self, purchases: PurchaseRepositoryPort) -> None:
        self._purchases = purchases

    async def execute(self, cmd: RecordBeaconInput) -> bool:
        """Returns ``True`` when the purchase was updated, ``False`` otherwise."""
        if not cmd.purchase_id or not cmd.provider_tx_id:
            return False

        purchase = await self._purchases.get(cmd.purchase_id)
        if purchase is None:
            return False
        if purchase.status is PurchaseStatus.SUCCESS:
            return False
        if purchase.payment_ref.provider_tx_id:
            return False

        now = datetime.now(timezone.utc).isoformat()
        updated = purchase.with_payment_ref(
            PaymentReference(provider=purchase.payment_ref.provider, provider_tx_id=cmd.provider_tx_id)
        ).merge_payment_metadata(
            beacon_transaction_id=cmd.provider_tx_id,
            beacon_received_at=now,
        )
        await self._purchases.save(updated)
        log.info("Beacon recorded transactionId for %s", cmd.purchase_id)
        return True
