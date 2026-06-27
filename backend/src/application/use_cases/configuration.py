"""
Runtime configuration use cases.

- :class:`GetConfiguration` returns every section's *effective* (resolved)
  non-secret values plus, per secret field, a boolean telling whether a value
  is configured. Secret values themselves are never returned.
- :class:`UpdateConfigurationSection` validates an incoming section payload,
  encrypts its secret fields, and persists it. A secret left blank keeps the
  stored one ("leave blank to keep" semantics).
- :class:`TestSmtp` / :class:`TestSms` send a test message through the
  *currently resolved* configuration so an admin can confirm credentials.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.application.config.resolver import ConfigResolver
from src.application.config.schemas import CONFIG_SCHEMAS, SmtpConfig
from src.application.ports import SettingsRepositoryPort, SmsNotificationPort
from src.domain import ConfigSection
from src.infrastructure.config.crypto import decrypt, encrypt


class UnknownConfigSection(Exception):
    pass


class SmtpNotConfigured(Exception):
    pass


class SmsNotConfigured(Exception):
    pass


class GetConfiguration:
    def __init__(self, repo: SettingsRepositoryPort, env_settings) -> None:
        self._resolver = ConfigResolver(repo, env_settings)

    async def execute(self) -> dict[str, dict]:
        cfg = await self._resolver.resolve()
        sections = {
            ConfigSection.GENERAL.value: cfg.general,
            ConfigSection.SMTP.value: cfg.smtp,
            ConfigSection.KKIAPAY.value: cfg.kkiapay,
            ConfigSection.CINETPAY.value: cfg.cinetpay,
            ConfigSection.SMS.value: cfg.sms,
        }
        return {
            name: {"values": schema.public_values(), "secrets": schema.secret_status()} for name, schema in sections.items()
        }


class UpdateConfigurationSection:
    def __init__(self, repo: SettingsRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, section: ConfigSection, incoming: dict) -> dict:
        schema_cls = CONFIG_SCHEMAS.get(section)
        if schema_cls is None:
            raise UnknownConfigSection(section)

        existing = await self._repo.get(section) or {}

        # Build the plaintext view, then validate it with the section schema.
        plain: dict = {}
        for field in schema_cls.model_fields:
            if field in schema_cls.SECRET_FIELDS:
                if incoming.get(field):
                    plain[field] = incoming[field]
                elif existing.get(field):
                    plain[field] = decrypt(existing[field])
                # else: omit → schema default ("")
            elif field in incoming:
                plain[field] = incoming[field]
            elif field in existing:
                plain[field] = existing[field]

        validated = schema_cls(**{k: v for k, v in plain.items() if v is not None})

        # Persist with secret fields encrypted.
        stored = validated.model_dump()
        for field in schema_cls.SECRET_FIELDS:
            stored[field] = encrypt(stored[field]) if stored[field] else ""
        await self._repo.set(section, stored)

        return {"values": validated.public_values(), "secrets": validated.secret_status()}


class TestSmtp:
    def __init__(self, sender: Callable[..., None]) -> None:
        # ``sender(msg, host, port, user, password)`` — injected by the
        # composition root so this use case has no infrastructure import.
        self._sender = sender

    async def execute(self, smtp: SmtpConfig, to: str) -> None:
        if not smtp.host or not smtp.user:
            raise SmtpNotConfigured()
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "CaaS — test SMTP"
        msg["From"] = smtp.from_email
        msg["To"] = to
        msg.attach(MIMEText("Ceci est un email de test envoyé depuis la configuration CaaS.", "plain", "utf-8"))
        await asyncio.to_thread(self._sender, msg, smtp.host, smtp.port, smtp.user, smtp.password)


class TestSms:
    def __init__(self, sms: SmsNotificationPort) -> None:
        self._sms = sms

    async def execute(self, to: str, body: str | None = None) -> None:
        await self._sms.send(to, body or "CaaS — SMS de test.")
