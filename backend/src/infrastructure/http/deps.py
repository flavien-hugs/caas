"""
Composition root.

Manual wiring of use cases to their port implementations. Keeping this in one
module instead of a DI container makes the dependency graph readable at a
glance — each request-scoped dependency is a plain function returning a
fully-constructed use case.

Tests override the persistence factory by mutating
:func:`set_session_factory`; production reads ``DATABASE_URL`` from settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.config import ConfigResolver, ResolvedConfig
from src.application.ports import NotificationPort, PaymentProviderPort, SmsNotificationPort
from src.application.use_cases import (
    AdminConfirmPayment,
    ComputeDashboardStats,
    ComputeRevenueChart,
    ConfirmPayment,
    CreatePage,
    CreateUser,
    DeletePage,
    DeleteUser,
    ExportTransactions,
    GetConfiguration,
    GetPage,
    GetPublishedPageBySlug,
    GetUser,
    InitiatePurchase,
    ListPages,
    ListRecentFeedbacks,
    ListTransactions,
    ListUsers,
    LookupPurchase,
    PublishPage,
    ReconcilePending,
    RecordBeacon,
    ResendDelivery,
    SubmitFeedback,
    TestSms,
    TestSmtp,
    UnpublishPage,
    UpdateConfigurationSection,
    UpdatePage,
    UpdateUser,
)
from src.domain import PaymentProviderName
from src.infrastructure.config.settings import settings
from src.infrastructure.notification.no_op import NoOpNotification
from src.infrastructure.notification.product_catalog import InMemoryProductRepository
from src.infrastructure.notification.smtp_email import (
    SmtpEmailNotification,
    _default_send_smtp_message,
    build_email_jinja_env,
)
from src.infrastructure.payment.cinetpay import CinetpayProvider
from src.infrastructure.payment.kkiapay import KkiapayProvider
from src.infrastructure.persistence.feedback_repository import SqlFeedbackRepository
from src.infrastructure.persistence.page_repository import SqlPageRepository
from src.infrastructure.persistence.purchase_repository import SqlPurchaseRepository
from src.infrastructure.persistence.session import get_session_factory
from src.infrastructure.persistence.settings_repository import SqlAppSettingsRepository
from src.infrastructure.persistence.user_repository import SqlUserRepository
from src.infrastructure.sms.http_sms import HttpSmsProvider
from src.infrastructure.sms.no_op import NoOpSms

_session_factory_override: async_sessionmaker[AsyncSession] | None = None


def set_session_factory(factory: async_sessionmaker[AsyncSession] | None) -> None:
    """Allow tests to swap the persistence root for an in-memory engine."""
    global _session_factory_override
    _session_factory_override = factory


def _session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory_override is not None:
        return _session_factory_override
    return get_session_factory()


def _provider_name() -> PaymentProviderName:
    # Deployment-wide label for the purchase repository (provider isn't
    # persisted per-row in phase 1). The *active* provider for initiation /
    # verification is resolved from config in :func:`_payment_provider`.
    return PaymentProviderName(settings.PAYMENT_PROVIDER)


def _purchase_repository() -> SqlPurchaseRepository:
    return SqlPurchaseRepository(session_factory=_session_factory(), provider=_provider_name())


def _product_repository() -> InMemoryProductRepository:
    return InMemoryProductRepository(settings)


def settings_repository() -> SqlAppSettingsRepository:
    """Exposed publicly so the settings routes resolve it via ``Depends`` and
    tests override the session factory transparently."""
    return SqlAppSettingsRepository(session_factory=_session_factory())


async def build_resolved_config() -> ResolvedConfig:
    """Resolve effective config (DB > env). Usable outside HTTP (CLI/worker)."""
    return await ConfigResolver(settings_repository(), settings).resolve()


async def resolved_config() -> ResolvedConfig:
    """Request-scoped resolved configuration."""
    return await build_resolved_config()


def _payment_provider(cfg: ResolvedConfig) -> PaymentProviderPort:
    if cfg.payment_provider == PaymentProviderName.CINETPAY.value:
        return CinetpayProvider(
            site_id=cfg.cinetpay.site_id,
            api_key=cfg.cinetpay.api_key,
            sandbox=cfg.cinetpay.sandbox,
        )
    return KkiapayProvider(
        public_key=cfg.kkiapay.public_key,
        private_key=cfg.kkiapay.private_key,
        secret_key=cfg.kkiapay.secret_key,
        sandbox=cfg.kkiapay.sandbox,
        base_url=settings.KKIAPAY_URL,
        sandbox_url=settings.KKIAPAY_SANDBOX_URL,
        status_path=settings.KKIAPAY_TRANSACTION_STATUS_URL,
    )


def _sms(cfg: ResolvedConfig) -> SmsNotificationPort:
    if not cfg.sms.provider_url:
        return NoOpSms()
    return HttpSmsProvider(
        provider_url=cfg.sms.provider_url,
        api_key=cfg.sms.api_key,
        sender=cfg.sms.sender,
    )


@lru_cache
def _email_templates_dir() -> str:
    """
    Absolute path to the email templates directory shipped with the package.
    """
    return str(Path(__file__).resolve().parent.parent.parent.parent / "infrastructure" / "notification" / "email_templates")


def _notification(cfg: ResolvedConfig) -> NotificationPort:
    """Pick the right delivery adapter based on the resolved SMTP config.

    SMTP non configuré → NoOpNotification (dev/test/CI gracieux).
    SMTP configuré → SmtpEmailNotification.
    """
    if not cfg.smtp.host or not cfg.smtp.user:
        return NoOpNotification()
    return SmtpEmailNotification(
        products=_product_repository(),
        smtp_host=cfg.smtp.host,
        smtp_port=cfg.smtp.port,
        smtp_user=cfg.smtp.user,
        smtp_password=cfg.smtp.password,
        smtp_from=cfg.smtp.from_email,
        jinja_env=build_email_jinja_env(_email_templates_dir()),
    )


async def initiate_purchase_use_case(cfg: ResolvedConfig = Depends(resolved_config)) -> InitiatePurchase:
    return InitiatePurchase(
        purchases=_purchase_repository(),
        products=_product_repository(),
        provider=_payment_provider(cfg),
        provider_name=_provider_name(),
    )


def lookup_purchase_use_case() -> LookupPurchase:
    return LookupPurchase(purchases=_purchase_repository())


def record_beacon_use_case() -> RecordBeacon:
    return RecordBeacon(purchases=_purchase_repository())


def build_confirm_payment(cfg: ResolvedConfig) -> ConfirmPayment:
    return ConfirmPayment(
        purchases=_purchase_repository(),
        products=_product_repository(),
        provider=_payment_provider(cfg),
        notification=_notification(cfg),
    )


async def confirm_payment_use_case(cfg: ResolvedConfig = Depends(resolved_config)) -> ConfirmPayment:
    return build_confirm_payment(cfg)


def _feedback_repository() -> SqlFeedbackRepository:
    return SqlFeedbackRepository(session_factory=_session_factory())


def submit_feedback_use_case() -> SubmitFeedback:
    return SubmitFeedback(feedbacks=_feedback_repository())


def list_recent_feedbacks_use_case() -> ListRecentFeedbacks:
    return ListRecentFeedbacks(feedbacks=_feedback_repository())


def list_transactions_use_case() -> ListTransactions:
    return ListTransactions(purchases=_purchase_repository())


def compute_dashboard_stats_use_case() -> ComputeDashboardStats:
    return ComputeDashboardStats(purchases=_purchase_repository())


def compute_revenue_chart_use_case() -> ComputeRevenueChart:
    return ComputeRevenueChart(purchases=_purchase_repository())


async def resend_delivery_use_case(cfg: ResolvedConfig = Depends(resolved_config)) -> ResendDelivery:
    return ResendDelivery(purchases=_purchase_repository(), notification=_notification(cfg))


async def admin_confirm_payment_use_case(cfg: ResolvedConfig = Depends(resolved_config)) -> AdminConfirmPayment:
    return AdminConfirmPayment(
        purchases=_purchase_repository(),
        confirm=build_confirm_payment(cfg),
    )


def export_transactions_use_case() -> ExportTransactions:
    return ExportTransactions(purchases=_purchase_repository())


def user_repository() -> SqlUserRepository:
    """Exposed publicly: the login route and admin user CRUD routes resolve
    it via ``Depends(user_repository)`` so tests can override the session
    factory transparently."""
    return SqlUserRepository(session_factory=_session_factory())


def create_user_use_case() -> CreateUser:
    return CreateUser(users=user_repository())


def update_user_use_case() -> UpdateUser:
    return UpdateUser(users=user_repository())


def delete_user_use_case() -> DeleteUser:
    return DeleteUser(users=user_repository())


def list_users_use_case() -> ListUsers:
    return ListUsers(users=user_repository())


def get_user_use_case() -> GetUser:
    return GetUser(users=user_repository())


def _page_repository() -> SqlPageRepository:
    return SqlPageRepository(session_factory=_session_factory())


def create_page_use_case() -> CreatePage:
    return CreatePage(pages=_page_repository())


def update_page_use_case() -> UpdatePage:
    return UpdatePage(pages=_page_repository())


def delete_page_use_case() -> DeletePage:
    return DeletePage(pages=_page_repository())


def list_pages_use_case() -> ListPages:
    return ListPages(pages=_page_repository())


def get_page_use_case() -> GetPage:
    return GetPage(pages=_page_repository())


def publish_page_use_case() -> PublishPage:
    return PublishPage(pages=_page_repository())


def unpublish_page_use_case() -> UnpublishPage:
    return UnpublishPage(pages=_page_repository())


def get_published_page_by_slug_use_case() -> GetPublishedPageBySlug:
    return GetPublishedPageBySlug(pages=_page_repository())


def build_reconcile_pending(cfg: ResolvedConfig) -> ReconcilePending:
    """
    Reuses ConfirmPayment as the per-row delegate — one source of truth for
    verify + amount-check + delivery across the HTTP callback and the CLI.
    """
    return ReconcilePending(
        purchases=_purchase_repository(),
        confirm=build_confirm_payment(cfg),
    )


async def reconcile_pending_use_case(cfg: ResolvedConfig = Depends(resolved_config)) -> ReconcilePending:
    return build_reconcile_pending(cfg)


# --- Runtime configuration use cases ----------------------------------------


def get_configuration_use_case() -> GetConfiguration:
    return GetConfiguration(settings_repository(), settings)


def update_configuration_use_case() -> UpdateConfigurationSection:
    return UpdateConfigurationSection(settings_repository())


def test_smtp_use_case() -> TestSmtp:
    return TestSmtp(_default_send_smtp_message)


async def test_sms_use_case(cfg: ResolvedConfig = Depends(resolved_config)) -> TestSms:
    return TestSms(_sms(cfg))
