from __future__ import annotations

from typing import Any, Protocol

from src.domain import Purchase


class PaymentProviderPort(Protocol):
    """
    Outbound port to a payment gateway (Kkiapay, CinetPay, …).

    Implementations live in ``infrastructure/payment/``. Use cases depend on
    this Protocol only — never on a concrete provider.
    """

    async def initiate_payment(self, purchase: Purchase) -> str:
        """
        Return the URL (or widget render URL) the customer must be sent to.
        """
        ...

    async def verify_payment(self, provider_tx_id: str) -> dict[str, Any]:
        """
        Authoritative server-to-server status check.

        Must return at minimum a ``"status"`` key with one of
        ``"SUCCESS" | "FAILED" | "PENDING"``. Should also expose ``"amount"``
        when the provider reports it (used to re-validate the paid amount in
        :class:`ConfirmPayment`).
        """
        ...
