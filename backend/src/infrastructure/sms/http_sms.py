"""
Generic HTTP SMS provider.

Phase 1 scaffold: POSTs ``{sender, to, message}`` as JSON to a configurable
endpoint with a bearer API key. Most West-African SMS gateways accept a shape
close to this; the exact field names become configurable when a concrete
provider is wired. For now it gives the "test SMS" admin action something real
to call.
"""

from __future__ import annotations

import httpx


class HttpSmsProvider:
    def __init__(
        self,
        provider_url: str,
        api_key: str,
        sender: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._url = provider_url
        self._api_key = api_key
        self._sender = sender
        self._injected_client = http_client

    async def send(self, to: str, body: str) -> None:
        headers = {"Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        payload = {"sender": self._sender, "to": to, "message": body}

        if self._injected_client is not None:
            response = await self._injected_client.post(self._url, json=payload, headers=headers)
            response.raise_for_status()
            return

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self._url, json=payload, headers=headers)
            response.raise_for_status()
