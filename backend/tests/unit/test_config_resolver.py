"""ConfigResolver merge semantics: DB > env, secret fallback, masking."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.application.config import ConfigResolver
from src.domain import ConfigSection
from src.infrastructure.config.crypto import encrypt


def _env(**overrides):
    base = dict(
        PAYMENT_PROVIDER="kkiapay",
        SITE_URL="http://env",
        SMTP_HOST="env-host",
        SMTP_PORT=587,
        SMTP_USER="env-user",
        SMTP_PASSWORD="env-pass",
        SMTP_FROM="env@from",
        KKIAPAY_PUBLIC_KEY="pub",
        KKIAPAY_PRIVATE_KEY="env-priv",
        KKIAPAY_SECRET_KEY="env-sec",
        KKIAPAY_SANDBOX=True,
        CINETPAY_SITE_ID="",
        CINETPAY_API_KEY="",
        CINETPAY_SANDBOX=True,
        SMS_PROVIDER_URL="",
        SMS_API_KEY="",
        SMS_SENDER="",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class FakeSettingsRepo:
    def __init__(self, data: dict | None = None) -> None:
        self._data = data or {}

    async def get(self, section: ConfigSection):
        return self._data.get(section.value)

    async def set(self, section: ConfigSection, values: dict) -> None:
        self._data[section.value] = values

    async def all(self) -> dict[str, dict]:
        return dict(self._data)


@pytest.mark.asyncio
async def test_env_defaults_when_db_empty():
    cfg = await ConfigResolver(FakeSettingsRepo(), _env()).resolve()
    assert cfg.smtp.host == "env-host"
    assert cfg.smtp.password == "env-pass"
    assert cfg.payment_provider == "kkiapay"


@pytest.mark.asyncio
async def test_db_overrides_non_secret():
    repo = FakeSettingsRepo({"smtp": {"host": "db-host", "user": "db-user", "from_email": "db@from", "port": 25}})
    cfg = await ConfigResolver(repo, _env()).resolve()
    assert cfg.smtp.host == "db-host"
    assert cfg.smtp.port == 25


@pytest.mark.asyncio
async def test_db_secret_decrypted_and_used():
    repo = FakeSettingsRepo({"smtp": {"host": "db-host", "user": "u", "password": encrypt("db-pass")}})
    cfg = await ConfigResolver(repo, _env()).resolve()
    assert cfg.smtp.password == "db-pass"


@pytest.mark.asyncio
async def test_empty_db_secret_falls_back_to_env():
    repo = FakeSettingsRepo({"smtp": {"host": "db-host", "user": "u", "password": ""}})
    cfg = await ConfigResolver(repo, _env(SMTP_PASSWORD="env-pass")).resolve()
    assert cfg.smtp.password == "env-pass"


@pytest.mark.asyncio
async def test_provider_selection_from_db():
    repo = FakeSettingsRepo({"general": {"payment_provider": "cinetpay", "site_url": "http://x"}})
    cfg = await ConfigResolver(repo, _env()).resolve()
    assert cfg.payment_provider == "cinetpay"


def test_schema_masking_hides_secret_values():
    from src.application.config.schemas import SmtpConfig

    smtp = SmtpConfig(host="h", user="u", password="secret")
    assert "password" not in smtp.public_values()
    assert smtp.secret_status() == {"password": True}
    assert SmtpConfig(host="h").secret_status() == {"password": False}
