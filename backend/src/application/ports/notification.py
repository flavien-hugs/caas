from __future__ import annotations

from typing import Protocol

from src.domain import Purchase


class NotificationPort(Protocol):
    """
    Outbound delivery channel (email, WhatsApp shoulder-tap, …).

    The use case :class:`ConfirmPayment` calls ``deliver`` exactly once per
    successful purchase, after the row's idempotency flag has been checked.
    """

    async def deliver(self, purchase: Purchase) -> None: ...
