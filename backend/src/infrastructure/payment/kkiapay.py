"""
Kkiapay adapter — implements :class:`PaymentProviderPort`.

Behaviour preserved from ``app/providers/kkiapay/client.py``:

- ``initiate_payment`` returns a render URL pointing at the SvelteKit widget
  route. Kkiapay is a JS-widget-based gateway, so initiation is server-side
  trivial — the heavy lifting happens client-side and comes back via the
  callback redirect.
- ``verify_payment`` issues an authoritative status check against Kkiapay's
  Transaction Status API. The legacy ``app/`` already speaks this protocol;
  we keep the same request shape.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from src.domain import Purchase


class KkiapayProvider:
    def __init__(
        self,
        *,
        public_key: str,
        private_key: str,
        secret_key: str,
        sandbox: bool,
        base_url: str,
        sandbox_url: str,
        status_path: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        # Credentials + sandbox come from the resolved config (DB > env); the
        # API URLs stay env-keyed. Allow tests to inject a transport; production
        # builds a fresh client per verify call (verifies are infrequent).
        self._public_key = public_key
        self._private_key = private_key
        self._secret_key = secret_key
        self._sandbox = sandbox
        self._base_url = base_url
        self._sandbox_url = sandbox_url
        self._status_path = status_path
        self._injected_client = http_client

    async def initiate_payment(self, purchase: Purchase) -> str:
        return f"/v2/payment/render/{purchase.id}"

    async def verify_payment(self, provider_tx_id: str) -> dict[str, Any]:
        base_url = self._sandbox_url if self._sandbox else self._base_url
        url = urljoin(base_url, self._status_path)

        headers = {
            "Accept": "application/json",
            "X-SECRET-KEY": self._secret_key or "",
            "X-API-KEY": self._public_key or "",
            "X-PRIVATE-KEY": self._private_key or "",
        }
        payload = {"transactionId": provider_tx_id}

        if self._injected_client is not None:
            response = await self._injected_client.post(url, json=payload, headers=headers)
            return response.json()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.json()
