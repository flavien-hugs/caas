"""
No-op NotificationPort implementation.

Phase 1 only ships the fraude webinaire, whose access is delivered through
the SvelteKit success page (WhatsApp group link displayed inline). No email
or other backend-side delivery is required.

When the next product migrates (multi-business, batir-empire, …) we'll
introduce an :class:`SmtpEmailNotification` adapter and route by
``Product.delivery_method`` in the composition root.
"""

from __future__ import annotations

import logging

from src.domain import Purchase

log = logging.getLogger(__name__)


class NoOpNotification:
    async def deliver(self, purchase: Purchase) -> None:
        log.info("No-op delivery for %s (book_id=%s)", purchase.id, purchase.book_id)
