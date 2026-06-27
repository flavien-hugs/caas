from __future__ import annotations

from typing import Protocol


class SmsNotificationPort(Protocol):
    """Outbound port to an SMS gateway.

    Phase 1 scaffold: a single ``send`` used by the "test SMS" admin action.
    No business flow wires it yet — adding SMS as a delivery channel is a
    follow-up that depends only on this Protocol.
    """

    async def send(self, to: str, body: str) -> None: ...
