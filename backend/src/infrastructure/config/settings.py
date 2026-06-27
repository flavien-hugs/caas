__all__ = ["settings"]

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "caas"
    APP_VERSION: str = "0.1.0"
    HIDE_DOCS: bool = True
    ENVIRONMENT: Literal["dev", "staging", "production"] = Field(default="dev")
    LOG_LEVEL: str = Field(default="INFO")

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/caas",
    )

    REDIS_URL: str = Field(default="redis://redis:6379/0")
    REDIS_NAMESPACE: str = Field(default="v2")

    CELERY_BROKER_URL: str = Field(default="redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://redis:6379/0")
    CELERY_DEFAULT_QUEUE: str = Field(default="v2_default")

    PAYMENT_PROVIDER: Literal["kkiapay", "cinetpay"] = Field(default="kkiapay")

    # Kkiapay credentials — env-keyed in phase 1 (single tenant per deploy),
    # moves to per-tenant DB rows in phase 2.
    KKIAPAY_PUBLIC_KEY: Optional[str] = Field(default=None)
    KKIAPAY_PRIVATE_KEY: Optional[str] = Field(default=None)
    KKIAPAY_SECRET_KEY: Optional[str] = Field(default=None)
    KKIAPAY_URL: str = Field(default="https://api.kkiapay.me")
    KKIAPAY_SANDBOX_URL: str = Field(default="https://api-sandbox.kkiapay.me")
    KKIAPAY_TRANSACTION_STATUS_URL: str = Field(default="/api/v1/transactions/status")
    KKIAPAY_SANDBOX: bool = Field(default=True)

    # CinetPay credentials — env defaults; the DB config (section "cinetpay")
    # overrides them at runtime. Provider selection lives in the "general"
    # section / ``PAYMENT_PROVIDER``.
    CINETPAY_SITE_ID: Optional[str] = Field(default=None)
    CINETPAY_API_KEY: Optional[str] = Field(default=None)
    CINETPAY_SANDBOX: bool = Field(default=True)

    # SMS — env defaults; the DB config (section "sms") overrides them. Empty
    # provider URL disables SMS (NoOpSms).
    SMS_PROVIDER_URL: str = Field(default="")
    SMS_API_KEY: Optional[str] = Field(default=None)
    SMS_SENDER: str = Field(default="")

    # Fernet key used to encrypt config secrets at rest. Required in
    # production; falls back to a key derived from SESSION_SECRET in dev.
    CONFIG_ENCRYPTION_KEY: str = Field(default="")

    # Product catalog (phase 1: hard-coded for the first migrated product).
    FRAUDE_WEBINAIRE_PRICE: int = Field(default=10_000)
    FRAUDE_WHATSAPP_GROUP_LINK: str = Field(default="#")

    # SMTP — same env-var names as legacy app/ so a single .env serves both
    # during the strangler phase. Empty SMTP_HOST disables email delivery and
    # the composition root falls back to NoOpNotification.
    SMTP_HOST: str = Field(default="")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM: str = Field(default="no-reply@sbbsconsulting.com")

    ADMIN_USERNAME: str = Field(default="admin")
    ADMIN_PASSWORD: str = Field(default="admin")

    # sessions
    # MUST be overridden in staging/prod with a long random value. Empty in
    # dev triggers an unsafe in-process random secret with a startup warning
    # so a forgotten env doesn't silently degrade security.
    SESSION_SECRET: str = Field(default="")
    SESSION_TTL_SECONDS: int = Field(default=60 * 60 * 24 * 7)
    SESSION_COOKIE_NAME: str = Field(default="caas_session")
    SESSION_COOKIE_SECURE: bool = Field(default=False)

    SITE_URL: str = Field(default="http://localhost:8080")

    # Rate limit on the public POST /purchases endpoint. Mirrors the legacy
    # ``app/routers/payment.py`` ``@limiter.limit("3/minute")``. Set to an
    # empty string to disable (load tests, smoke runs).
    PURCHASES_RATE_LIMIT: str = Field(default="3/minute")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
