"""No-op SMS adapter — used when no SMS provider URL is configured."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


class NoOpSms:
    async def send(self, to: str, body: str) -> None:
        log.info("NoOpSms.send(to=%s) — SMS provider not configured, message dropped.", to)
