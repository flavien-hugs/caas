"""
Unit tests for :class:`SmtpEmailNotification`.

No SMTP server, no filesystem: the sender is a spy callable and the Jinja
environment is built on a :class:`DictLoader` so the test template lives
inline. This lets us assert on:

- the produced ``MIMEMultipart`` (subject, from, to, plain part, HTML part);
- the Jinja filters ``format_price`` / ``format_datetime`` actually applying
  (preventing the silent fallback-to-plain bug from the legacy ``app/``
  Jinja env that we fixed by mirroring the filter registrations);
- the no-SMTP and not-an-email-product short-circuits.
"""

from __future__ import annotations

import pytest
from jinja2 import DictLoader, Environment

from src.domain import (
    Currency,
    Customer,
    DeliveryMethod,
    EmailConfig,
    Money,
    PaymentProviderName,
    PaymentReference,
    Product,
    Purchase,
    PurchaseStatus,
    format_datetime,
    format_price,
)
from src.infrastructure.notification.smtp_email import SmtpEmailNotification

HTML_TEMPLATE = """
<html><body>
<p>Bonjour {{ name }},</p>
<p>Pack: {{ pack_name }}</p>
<p>Montant: {{ amount|format_price }} {{ currency }}</p>
<p>Ref: {{ transaction_id }}</p>
<p>Lien: <a href="{{ drive_link }}">accéder</a></p>
</body></html>
""".strip()


def _build_env() -> Environment:
    env = Environment(loader=DictLoader({"test_email.html": HTML_TEMPLATE}), autoescape=True)
    env.filters["format_price"] = format_price
    env.filters["format_datetime"] = format_datetime
    return env


def _purchase() -> Purchase:
    return Purchase(
        id="pid_1",
        book_id="multi-business",
        customer=Customer(email="buyer@example.com", name="Aïcha Koné", phone="+225", country="CI", city="Abidjan"),
        amount=Money(amount=7_000, currency=Currency.XOF),
        status=PurchaseStatus.SUCCESS,
        payment_ref=PaymentReference(provider=PaymentProviderName.KKIAPAY, provider_tx_id="kkia_123"),
    )


def _email_product() -> Product:
    return Product(
        book_id="multi-business",
        name="Pack Gestion Multi-Business",
        price=Money(amount=7_000, currency=Currency.XOF),
        delivery_method=DeliveryMethod.EMAIL,
        delivery_payload="https://drive.example.com/pack",
        email_config=EmailConfig(
            subject="Paiement confirmé — votre pack",
            template_path="test_email.html",
            welcome_text="Paiement confirmé, votre pack est prêt.",
            cta_label="Accédez à votre pack",
        ),
    )


class FakeProducts:
    def __init__(self, by_id: dict[str, Product]) -> None:
        self.by_id = by_id

    async def get(self, book_id: str) -> Product | None:
        return self.by_id.get(book_id)


@pytest.mark.asyncio
async def test_delivers_renders_html_and_calls_smtp_sender():
    captured: list[tuple] = []

    def spy_sender(msg, host, port, user, password):
        captured.append((msg, host, port, user, password))

    purchase = _purchase()
    # SUCCESS status is irrelevant for the adapter (the use case decides).
    notif = SmtpEmailNotification(
        products=FakeProducts({"multi-business": _email_product()}),
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user",
        smtp_password="pass",
        smtp_from="no-reply@example.com",
        jinja_env=_build_env(),
        sender=spy_sender,
    )

    await notif.deliver(purchase)

    assert len(captured) == 1
    msg, host, port, user, password = captured[0]
    assert host == "smtp.example.com"
    assert port == 587
    assert user == "user"
    assert password == "pass"
    assert msg["Subject"] == "Paiement confirmé — votre pack"
    assert msg["From"] == "no-reply@example.com"
    assert msg["To"] == "buyer@example.com"

    payload = msg.get_payload()
    assert len(payload) == 2  # plain + html
    plain, html = payload
    assert plain.get_content_type() == "text/plain"
    assert html.get_content_type() == "text/html"

    plain_text = plain.get_payload(decode=True).decode()
    assert "Bonjour Aïcha" in plain_text
    assert "Paiement confirmé, votre pack est prêt." in plain_text
    assert "https://drive.example.com/pack" in plain_text

    html_text = html.get_payload(decode=True).decode()
    # The format_price filter must apply (otherwise legacy would fall back
    # silently to plain only — the bug we explicitly fixed in this port).
    assert "7 000 XOF" in html_text
    assert "kkia_123" in html_text
    assert "Pack Gestion Multi-Business" in html_text


@pytest.mark.asyncio
async def test_skips_when_smtp_not_configured():
    captured = []
    notif = SmtpEmailNotification(
        products=FakeProducts({"multi-business": _email_product()}),
        smtp_host="",  # ← not configured
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        smtp_from="no-reply@example.com",
        jinja_env=_build_env(),
        sender=lambda *a, **kw: captured.append(a),
    )
    await notif.deliver(_purchase())
    assert captured == []


@pytest.mark.asyncio
async def test_skips_when_product_is_not_email_delivery():
    captured = []
    whatsapp = Product(
        book_id="multi-business",
        name="X",
        price=Money(amount=7_000, currency=Currency.XOF),
        delivery_method=DeliveryMethod.WHATSAPP,  # ← not email
        email_config=None,
    )
    notif = SmtpEmailNotification(
        products=FakeProducts({"multi-business": whatsapp}),
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="u",
        smtp_password="p",
        smtp_from="f",
        jinja_env=_build_env(),
        sender=lambda *a, **kw: captured.append(a),
    )
    await notif.deliver(_purchase())
    assert captured == []


@pytest.mark.asyncio
async def test_falls_back_to_plain_only_when_template_render_fails():
    captured = []
    bad_env = Environment(loader=DictLoader({}), autoescape=True)  # template not found
    notif = SmtpEmailNotification(
        products=FakeProducts({"multi-business": _email_product()}),
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="u",
        smtp_password="p",
        smtp_from="f",
        jinja_env=bad_env,
        sender=lambda *a, **kw: captured.append(a),
    )
    await notif.deliver(_purchase())
    assert len(captured) == 1
    msg = captured[0][0]
    # Only the plain part survives the rendering failure.
    assert len(msg.get_payload()) == 1
    assert msg.get_payload()[0].get_content_type() == "text/plain"


def test_format_filters_byte_match_legacy():
    """Spot-check that the domain filters render exactly like ``app/core/ui``."""
    assert format_price(7000) == "7 000"
    assert format_datetime("2026-06-19T20:00:00Z") == "Vendredi 19 Juin 2026 à 20h00"
    assert format_datetime("2026-12-01T08:30:00Z") == "Mardi 01 Décembre 2026 à 08h30"
