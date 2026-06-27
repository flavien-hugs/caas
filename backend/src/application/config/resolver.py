"""
Resolve the effective runtime configuration: DB overrides over env defaults.

The composition root asks for a :class:`ResolvedConfig` once per request and
reads typed, decrypted sections from it (``cfg.smtp``, ``cfg.kkiapay``, …).
Each section is built by overlaying the stored DB blob (secrets encrypted) on
the env-keyed defaults, then decrypting secret fields. A secret left empty in
the DB falls back to the env value, so a partial DB config never wipes an
env-provided secret.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.application.config.schemas import (
    CinetpayConfig,
    GeneralConfig,
    KkiapayConfig,
    SmsConfig,
    SmtpConfig,
)
from src.application.ports import SettingsRepositoryPort
from src.domain import ConfigSection
from src.infrastructure.config.crypto import decrypt


@dataclass(frozen=True, slots=True)
class ResolvedConfig:
    general: GeneralConfig
    smtp: SmtpConfig
    kkiapay: KkiapayConfig
    cinetpay: CinetpayConfig
    sms: SmsConfig

    @property
    def payment_provider(self) -> str:
        return self.general.payment_provider


class ConfigResolver:
    def __init__(self, repo: SettingsRepositoryPort, env_settings) -> None:
        self._repo = repo
        self._s = env_settings

    def _env_defaults(self) -> dict[ConfigSection, dict]:
        s = self._s
        return {
            ConfigSection.GENERAL: {
                "payment_provider": s.PAYMENT_PROVIDER,
                "site_url": s.SITE_URL,
            },
            ConfigSection.SMTP: {
                "host": s.SMTP_HOST,
                "port": s.SMTP_PORT,
                "user": s.SMTP_USER,
                "password": s.SMTP_PASSWORD,
                "from_email": s.SMTP_FROM,
            },
            ConfigSection.KKIAPAY: {
                "public_key": s.KKIAPAY_PUBLIC_KEY or "",
                "private_key": s.KKIAPAY_PRIVATE_KEY or "",
                "secret_key": s.KKIAPAY_SECRET_KEY or "",
                "sandbox": s.KKIAPAY_SANDBOX,
            },
            ConfigSection.CINETPAY: {
                "site_id": s.CINETPAY_SITE_ID or "",
                "api_key": s.CINETPAY_API_KEY or "",
                "sandbox": s.CINETPAY_SANDBOX,
            },
            ConfigSection.SMS: {
                "provider_url": s.SMS_PROVIDER_URL,
                "api_key": s.SMS_API_KEY or "",
                "sender": s.SMS_SENDER,
            },
        }

    @staticmethod
    def _merge(schema_cls, env: dict, db: dict | None) -> dict:
        merged = dict(env)
        for key, value in (db or {}).items():
            if key in schema_cls.SECRET_FIELDS:
                decrypted = decrypt(value) if isinstance(value, str) else ""
                if decrypted:  # empty secret in DB → keep env fallback
                    merged[key] = decrypted
            else:
                merged[key] = value
        return merged

    async def resolve(self) -> ResolvedConfig:
        env = self._env_defaults()
        db = await self._repo.all()

        def build(section: ConfigSection, schema_cls):
            return schema_cls(**self._merge(schema_cls, env[section], db.get(section.value)))

        return ResolvedConfig(
            general=build(ConfigSection.GENERAL, GeneralConfig),
            smtp=build(ConfigSection.SMTP, SmtpConfig),
            kkiapay=build(ConfigSection.KKIAPAY, KkiapayConfig),
            cinetpay=build(ConfigSection.CINETPAY, CinetpayConfig),
            sms=build(ConfigSection.SMS, SmsConfig),
        )
