"""Outbound ports — Protocols the application layer depends on.

Use cases import these (never the concrete adapters in ``infrastructure/``).
Implementations are wired in :py:mod:`sbbs_checkout.infrastructure.http.deps`.
"""

from .cache import CachePort
from .feedback_repository import FeedbackRepositoryPort
from .notification import NotificationPort
from .page_repository import PageRepositoryPort
from .payment_provider import PaymentProviderPort
from .product_repository import ProductRepositoryPort
from .purchase_repository import PurchaseRepositoryPort
from .settings_repository import SettingsRepositoryPort
from .sms import SmsNotificationPort
from .user_repository import UserRepositoryPort

__all__ = [
    "CachePort",
    "FeedbackRepositoryPort",
    "NotificationPort",
    "PageRepositoryPort",
    "PaymentProviderPort",
    "ProductRepositoryPort",
    "PurchaseRepositoryPort",
    "SettingsRepositoryPort",
    "SmsNotificationPort",
    "UserRepositoryPort",
]
