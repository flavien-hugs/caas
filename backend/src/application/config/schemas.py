"""
Typed schema for each runtime-configurable section.

One Pydantic model per :class:`~src.domain.ConfigSection`. Each model declares
which of its fields are secret via the ``SECRET_FIELDS`` ClassVar. That single
declaration drives:

- masking on read (the API never returns a secret value, only a boolean
  "configured" flag);
- encryption at rest (the repository encrypts exactly these fields);
- "leave blank to keep" semantics on update.

Field names intentionally drop the section prefix (``host`` not ``smtp_host``)
since the section already namespaces them. The resolver maps them to/from the
legacy env vars.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from src.domain import ConfigSection


class ConfigSchema(BaseModel):
    """Base for every config section schema."""

    SECRET_FIELDS: ClassVar[frozenset[str]] = frozenset()

    model_config = {"extra": "ignore"}

    def public_values(self) -> dict:
        """Field values with secrets removed (safe to return to the client)."""
        return {k: v for k, v in self.model_dump().items() if k not in self.SECRET_FIELDS}

    def secret_status(self) -> dict[str, bool]:
        """Per-secret-field ``True`` when a non-empty value is configured."""
        return {f: bool(getattr(self, f)) for f in self.SECRET_FIELDS}


class GeneralConfig(ConfigSchema):
    payment_provider: Literal["kkiapay", "cinetpay"] = Field(default="kkiapay")
    site_url: str = Field(default="http://localhost:8080")


class SmtpConfig(ConfigSchema):
    SECRET_FIELDS = frozenset({"password"})

    host: str = Field(default="")
    port: int = Field(default=587)
    user: str = Field(default="")
    password: str = Field(default="")
    from_email: str = Field(default="no-reply@caas.com")


class KkiapayConfig(ConfigSchema):
    SECRET_FIELDS = frozenset({"private_key", "secret_key"})

    public_key: str = Field(default="")
    private_key: str = Field(default="")
    secret_key: str = Field(default="")
    sandbox: bool = Field(default=True)


class CinetpayConfig(ConfigSchema):
    SECRET_FIELDS = frozenset({"api_key"})

    site_id: str = Field(default="")
    api_key: str = Field(default="")
    sandbox: bool = Field(default=True)


class SmsConfig(ConfigSchema):
    SECRET_FIELDS = frozenset({"api_key"})

    provider_url: str = Field(default="")
    api_key: str = Field(default="")
    sender: str = Field(default="")


CONFIG_SCHEMAS: dict[ConfigSection, type[ConfigSchema]] = {
    ConfigSection.GENERAL: GeneralConfig,
    ConfigSection.SMTP: SmtpConfig,
    ConfigSection.KKIAPAY: KkiapayConfig,
    ConfigSection.CINETPAY: CinetpayConfig,
    ConfigSection.SMS: SmsConfig,
}
