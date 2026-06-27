from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique

from .money import Money


@unique
class DeliveryMethod(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class EmailConfig:
    """Per-product email-rendering config.

    Required when ``Product.delivery_method`` is :attr:`DeliveryMethod.EMAIL`;
    ignored otherwise. Mirrors the per-entry fields of the legacy
    ``PRODUCT_MAPPING`` in :py:mod:`app.services.mail` so existing templates
    can be ported verbatim.
    """

    subject: str
    template_path: str
    welcome_text: str
    cta_label: str


@dataclass(frozen=True, slots=True)
class Product:
    """
    Sellable product. Phase 1 = catalogue loaded from env-keyed config
    (matches the legacy book_id mapping); phase 2 = loaded from DB per tenant.
    """

    book_id: str
    name: str
    price: Money
    delivery_method: DeliveryMethod
    delivery_payload: str | None = None
    email_config: EmailConfig | None = None
