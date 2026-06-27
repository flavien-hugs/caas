"""
Runtime configuration sections.

Phase 1 made everything env-keyed (SMTP, payment aggregator credentials, …).
This enum names the configuration "sections" an admin can edit at runtime; the
typed schema for each section lives in ``application/config/schemas.py`` and the
DB-over-env merge in ``application/config/resolver.py``. The route layer never
hard-codes section names — it goes through :class:`ConfigSection`.
"""

from __future__ import annotations

from enum import StrEnum


class ConfigSection(StrEnum):
    GENERAL = "general"  # provider selection, site URL, …
    SMTP = "smtp"
    KKIAPAY = "kkiapay"
    CINETPAY = "cinetpay"
    SMS = "sms"
