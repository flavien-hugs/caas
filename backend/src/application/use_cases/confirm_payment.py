"""
Use case: confirm a payment with the provider and deliver the product.

Ported from :py:func:`app.routers.payment.payment_callback`. Logic preserved
verbatim because each guard maps to a concrete security or correctness
incident in production:

- ``security_error`` purchases are never resurrected (the legacy sync used to
  flip them back to ``SUCCESS`` on provider re-verify, which bypassed the
  amount-mismatch protection — fixed in cd1d2cc and preserved here);
- the paid amount is re-validated against the canonical ``Purchase.amount``
  with a 1-unit tolerance (mirrors the ``abs(paid - expected) > 1`` rule);
- delivery is idempotent: ``payment_metadata.email_sent`` (legacy flag name
  kept for compat with the existing rows) gates the notification call so
  re-runs don't notify twice;
- delivery is skipped for products whose ``DeliveryMethod`` is not ``EMAIL``
  (e.g. fraude webinaire = WHATSAPP, where access is shown on the success
  page directly).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.application.ports import (
    NotificationPort,
    PaymentProviderPort,
    ProductRepositoryPort,
    PurchaseRepositoryPort,
)
from src.domain import (
    DeliveryMethod,
    PaymentReference,
    Purchase,
    PurchaseStatus,
    extract_provider_amount,
)

log = logging.getLogger(__name__)

AMOUNT_TOLERANCE = 1  # XOF; matches the legacy callback tolerance


@dataclass(frozen=True, slots=True)
class ConfirmPaymentInput:
    purchase_id: str
    provider_tx_id: str


@dataclass(frozen=True, slots=True)
class ConfirmPaymentOutput:
    purchase: Purchase
    confirmed: bool  # True if SUCCESS after this run
    delivered: bool  # True if notification was dispatched


class PurchaseNotFound(Exception):
    pass


class ConfirmPayment:
    def __init__(
        self,
        purchases: PurchaseRepositoryPort,
        products: ProductRepositoryPort,
        provider: PaymentProviderPort,
        notification: NotificationPort,
    ) -> None:
        self._purchases = purchases
        self._products = products
        self._provider = provider
        self._notification = notification

    async def execute(self, cmd: ConfirmPaymentInput) -> ConfirmPaymentOutput:
        purchase = await self._purchases.get(cmd.purchase_id)
        if purchase is None:
            raise PurchaseNotFound(cmd.purchase_id)

        if purchase.has_security_error:
            log.warning("Skipping confirm for %s — flagged security_error", purchase.id)
            return ConfirmPaymentOutput(purchase=purchase, confirmed=False, delivered=False)

        try:
            cp_result: dict[str, Any] = await self._provider.verify_payment(cmd.provider_tx_id)
        except Exception as exc:
            log.exception("Provider verify failed for %s: %r", cmd.provider_tx_id, exc)
            return ConfirmPaymentOutput(purchase=purchase, confirmed=False, delivered=False)

        provider_status = cp_result.get("status")
        now = datetime.now(timezone.utc).isoformat()

        if provider_status != "SUCCESS":
            failed = purchase.with_status(PurchaseStatus.FAILED).merge_payment_metadata(
                **cp_result,
                last_check_at=now,
            )
            await self._purchases.save(failed)
            return ConfirmPaymentOutput(purchase=failed, confirmed=False, delivered=False)

        # Re-validate amount before confirming — the security anchor.
        paid_amount = extract_provider_amount(cp_result)
        if paid_amount is not None and abs(int(round(paid_amount)) - purchase.amount.amount) > AMOUNT_TOLERANCE:
            log.error(
                "CRITICAL amount mismatch on confirm for %s: paid=%s expected=%s",
                purchase.id,
                paid_amount,
                purchase.amount.amount,
            )
            blocked = purchase.with_status(PurchaseStatus.FAILED).merge_payment_metadata(
                **cp_result,
                security_error="amount_mismatch",
            )
            await self._purchases.save(blocked)
            return ConfirmPaymentOutput(purchase=blocked, confirmed=False, delivered=False)

        confirmed = (
            purchase.with_payment_ref(
                PaymentReference(provider=purchase.payment_ref.provider, provider_tx_id=cmd.provider_tx_id)
            )
            .with_status(PurchaseStatus.SUCCESS)
            .merge_payment_metadata(
                **cp_result,
                provider_id=cmd.provider_tx_id,
            )
        )

        delivered = False
        # Idempotency: legacy code keys delivery on payment_metadata.email_sent
        # — keep the same key so a row written by app/ stays compatible.
        if not confirmed.payment_metadata.get("email_sent"):
            product = await self._products.get(confirmed.book_id)
            if product is not None and product.delivery_method is DeliveryMethod.EMAIL:
                try:
                    await self._notification.deliver(confirmed)
                    confirmed = confirmed.merge_payment_metadata(email_sent=True, delivered_at=now)
                    delivered = True
                except Exception as exc:
                    log.exception("Notification delivery failed for %s: %r", confirmed.id, exc)
                    confirmed = confirmed.merge_payment_metadata(email_sent=False)

        await self._purchases.save(confirmed)
        return ConfirmPaymentOutput(purchase=confirmed, confirmed=True, delivered=delivered)
