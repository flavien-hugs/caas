"""
CinetPay adapter — scaffold implementing :class:`PaymentProviderPort`.

The config plumbing (credentials section, provider selection) is complete, but
the gateway protocol itself is a follow-up: ``verify_payment`` returns PENDING
rather than guessing a status, so selecting CinetPay never *confirms* a payment
on a half-built integration (safer than crashing the callback). Wire the real
``/v2/payment/check`` call here when finishing the integration.
"""

from __future__ import annotations

import logging
from typing import Any

from src.domain import Purchase

log = logging.getLogger(__name__)


class CinetpayProvider:
    def __init__(self, site_id: str, api_key: str, sandbox: bool = True) -> None:
        self._site_id = site_id
        self._api_key = api_key
        self._sandbox = sandbox

    async def initiate_payment(self, purchase: Purchase) -> str:
        return f"/v2/payment/render/{purchase.id}"

    async def verify_payment(self, provider_tx_id: str) -> dict[str, Any]:
        log.warning("CinetpayProvider.verify_payment is a scaffold — returning PENDING for tx=%s", provider_tx_id)
        return {"status": "PENDING"}
