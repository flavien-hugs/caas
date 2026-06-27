"""
Use case: initiate a purchase.

Ported from :py:func:`app.routers.payment.purchase`. Logic preserved:

- price is server-authoritative (looked up by ``book_id`` via the product
  catalog), the client-provided amount is never trusted;
- a price discrepancy is logged but the purchase still proceeds at the
  server-side price (security_alert in the legacy code);
- the row is persisted ``PENDING`` *before* calling the provider, so that
  even if the provider call blows up the row exists and is recoverable by
  the reconciliation job;
- on provider failure, the row is flipped to ``ERROR`` with the exception
  message stashed in ``payment_metadata`` and a domain-level
  ``ProviderInitiationFailed`` raised for the HTTP boundary to translate.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.application.ports import (
    PaymentProviderPort,
    ProductRepositoryPort,
    PurchaseRepositoryPort,
)
from src.domain import (
    Customer,
    Money,
    PaymentProviderName,
    PaymentReference,
    Purchase,
    PurchaseStatus,
)

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class InitiatePurchaseInput:
    book_id: str
    customer: Customer
    client_amount: int | None = None
    offer: str | None = None
    situation: str | None = None


@dataclass(frozen=True, slots=True)
class InitiatePurchaseOutput:
    purchase_id: str
    payment_url: str
    server_amount: Money


class UnknownProduct(Exception):
    """Raised when ``book_id`` does not match any catalog entry."""


class ProviderInitiationFailed(Exception):
    """Raised when the payment provider rejects the initiation."""


class InitiatePurchase:
    def __init__(
        self,
        purchases: PurchaseRepositoryPort,
        products: ProductRepositoryPort,
        provider: PaymentProviderPort,
        provider_name: PaymentProviderName,
    ) -> None:
        self._purchases = purchases
        self._products = products
        self._provider = provider
        self._provider_name = provider_name

    async def execute(self, cmd: InitiatePurchaseInput) -> InitiatePurchaseOutput:
        product = await self._products.get(cmd.book_id)
        if product is None:
            raise UnknownProduct(cmd.book_id)

        server_amount = product.price
        if cmd.client_amount is not None and abs(cmd.client_amount - server_amount.amount) > 0:
            log.warning(
                "Security alert: price discrepancy for %s book_id=%s client=%s server=%s",
                cmd.customer.email,
                cmd.book_id,
                cmd.client_amount,
                server_amount.amount,
            )

        client_metadata = {"offer": cmd.offer, "situation": cmd.situation}
        purchase = Purchase.new(
            book_id=cmd.book_id,
            customer=cmd.customer,
            amount=server_amount,
            payment_ref=PaymentReference(provider=self._provider_name),
            client_metadata=client_metadata,
        )
        await self._purchases.add(purchase)

        try:
            payment_url = await self._provider.initiate_payment(purchase)
            if not payment_url:
                raise ProviderInitiationFailed("provider returned an empty URL")
        except Exception as exc:
            log.exception("Payment initiation failed for %s: %r", purchase.id, exc)
            failed = purchase.with_status(PurchaseStatus.ERROR).merge_payment_metadata(
                initiation_error=str(exc),
            )
            await self._purchases.save(failed)
            raise ProviderInitiationFailed(str(exc)) from exc

        confirmed = purchase.merge_payment_metadata(checkout_url=str(payment_url))
        await self._purchases.save(confirmed)

        return InitiatePurchaseOutput(
            purchase_id=purchase.id,
            payment_url=str(payment_url),
            server_amount=server_amount,
        )
