"""
SMTP-backed :class:`NotificationPort` implementation.

Ported from :py:mod:`app.services.mail`. Same idempotent semantics, same
plain-text-then-HTML message structure, same async-via-thread send. The
fix from the security review is preserved: the Jinja environment carries
:py:func:`src.domain.format_price` and :py:func:`src.domain.format_datetime`
as filters, so HTML email rendering no longer silently falls back to the
plain-text body when a template uses them.

The actual SMTP send is performed through an injectable ``sender`` callable
so unit tests can capture the built ``MIMEMultipart`` without hitting a
network.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from collections.abc import Callable
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.application.ports import ProductRepositoryPort
from src.domain import (
    DeliveryMethod,
    Purchase,
    format_datetime,
    format_price,
)

log = logging.getLogger(__name__)

SmtpSender = Callable[[MIMEMultipart, str, int, str, str], None]


def _default_send_smtp_message(msg: MIMEMultipart, host: str, port: int, user: str, password: str) -> None:
    """Mirror of :py:func:`app.services.mail._send_smtp_message`."""
    if port == 465:
        with smtplib.SMTP_SSL(host, port) as server:
            server.login(user, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)


def build_email_jinja_env(templates_dir: str) -> Environment:
    """Build a Jinja env preloaded with the domain formatting filters.

    Centralizing this lets tests build a sandboxed env (in-memory loader, etc.)
    while production wiring just passes the on-disk template directory.
    """
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(enabled_extensions=("html",)),
    )
    env.filters["format_price"] = format_price
    env.filters["format_datetime"] = format_datetime
    return env


class SmtpEmailNotification:
    def __init__(
        self,
        products: ProductRepositoryPort,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        smtp_from: str,
        jinja_env: Environment,
        sender: SmtpSender | None = None,
    ) -> None:
        self._products = products
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_user = smtp_user
        self._smtp_password = smtp_password
        self._smtp_from = smtp_from
        self._env = jinja_env
        self._sender = sender or _default_send_smtp_message

    async def deliver(self, purchase: Purchase) -> None:
        """Render and send the confirmation email for *purchase*.

        Skips (with a log line, no exception) when the product isn't an email
        delivery or the catalog row is missing — defensive, since
        :class:`ConfirmPayment` already gates on ``delivery_method ==
        DeliveryMethod.EMAIL``.
        """
        if not self._smtp_host:
            log.info("SMTP not configured, skipping delivery for %s", purchase.id)
            return

        product = await self._products.get(purchase.book_id)
        if product is None or product.email_config is None or product.delivery_method is not DeliveryMethod.EMAIL:
            log.warning(
                "Skipping email delivery for %s — not an email product (book_id=%s)",
                purchase.id,
                purchase.book_id,
            )
            return

        cfg = product.email_config
        drive_link = product.delivery_payload or "#"
        first_name = (purchase.customer.name or "").split(" ")[0] or "Client"

        plain_body = (
            f"Bonjour {first_name},\n\n"
            f"{cfg.welcome_text}\n\n"
            f"{cfg.cta_label} : {drive_link}\n\n"
            "À votre succès,\n"
            "L'équipe SBBS Consulting"
        )

        html_body: str | None = None
        try:
            tmpl = self._env.get_template(cfg.template_path)
            html_body = tmpl.render(
                name=purchase.customer.name or first_name,
                transaction_id=purchase.payment_ref.provider_tx_id or purchase.id,
                drive_link=drive_link,
                pack_name=product.name,
                amount=purchase.amount.amount,
                currency=purchase.amount.currency.value,
            )
        except Exception as exc:
            log.warning("Could not render HTML email template %s: %r", cfg.template_path, exc)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = cfg.subject
        msg["From"] = self._smtp_from
        msg["To"] = purchase.customer.email
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            await asyncio.to_thread(
                self._sender,
                msg,
                self._smtp_host,
                self._smtp_port,
                self._smtp_user,
                self._smtp_password,
            )
            log.info("Email sent to %s for purchase %s", purchase.customer.email, purchase.id)
        except Exception:
            log.exception("Failed to send email to %s for purchase %s", purchase.customer.email, purchase.id)
            raise
