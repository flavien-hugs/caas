"""
Admin settings routes end-to-end.

Covers: RBAC guard, secret masking on read, update + persistence, the
"leave blank to keep" secret semantics, validation, and the SMTP/SMS test
actions (sender mocked).
"""

from __future__ import annotations

import base64

import pytest

from src.infrastructure.config.settings import settings


@pytest.fixture(autouse=True)
def _no_env_smtp(monkeypatch):
    """Neutralise the developer's real ``.env`` SMTP creds for this module so a
    ``/smtp/test`` never hits a real server. Tests that need SMTP configured do
    it through the API (DB) and mock the sender."""
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")


def _basic(username: str = "admin", password: str = "admin") -> dict:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


async def _login_role(client, *, username: str, role: str) -> None:
    r = await client.post(
        "/admin/users",
        json={"username": username, "password": "longpassword", "role": role},
        headers=_basic(),
    )
    assert r.status_code == 201, r.text
    client.cookies.clear()
    r2 = await client.post("/auth/login", json={"username": username, "password": "longpassword"})
    assert r2.status_code == 200, r2.text


@pytest.mark.asyncio
async def test_reader_cannot_access_settings(client, db_session_factory):
    await _login_role(client, username="bob", role="reader")
    r = await client.get("/admin/settings")
    assert r.status_code == 403, r.text
    assert "manage:settings" in r.json()["detail"]


@pytest.mark.asyncio
async def test_super_admin_reads_all_sections_with_secrets_masked(client, db_session_factory):
    r = await client.get("/admin/settings", headers=_basic())
    assert r.status_code == 200, r.text
    data = r.json()
    assert set(data) == {"general", "smtp", "kkiapay", "cinetpay", "sms"}
    # Secret values are never returned, only a configured flag.
    assert "password" not in data["smtp"]["values"]
    assert "password" in data["smtp"]["secrets"]


@pytest.mark.asyncio
async def test_update_smtp_persists_and_masks(client, db_session_factory):
    body = {"host": "smtp.example.com", "port": 2525, "user": "mailer", "password": "topsecret", "from_email": "no-reply@x"}
    r = await client.put("/admin/settings/smtp", json=body, headers=_basic())
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["values"]["host"] == "smtp.example.com"
    assert out["values"]["port"] == 2525
    assert "password" not in out["values"]
    assert out["secrets"]["password"] is True

    # Reload reflects the change, still masked.
    r2 = await client.get("/admin/settings/smtp", headers=_basic())
    assert r2.json()["values"]["host"] == "smtp.example.com"
    assert r2.json()["secrets"]["password"] is True


@pytest.mark.asyncio
async def test_secret_left_blank_is_kept(client, db_session_factory):
    await client.put(
        "/admin/settings/smtp",
        json={"host": "h1", "user": "u1", "password": "keepme", "from_email": "a@b"},
        headers=_basic(),
    )
    # Second update changes host only, no password → secret kept.
    r = await client.put(
        "/admin/settings/smtp",
        json={"host": "h2", "user": "u1", "from_email": "a@b"},
        headers=_basic(),
    )
    assert r.status_code == 200, r.text
    assert r.json()["values"]["host"] == "h2"
    assert r.json()["secrets"]["password"] is True


@pytest.mark.asyncio
async def test_invalid_provider_rejected(client, db_session_factory):
    r = await client.put(
        "/admin/settings/general",
        json={"payment_provider": "paypal", "site_url": "http://x"},
        headers=_basic(),
    )
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_cinetpay_blocked_in_production(client, db_session_factory, monkeypatch):
    # CinetPay is a scaffold (verify returns PENDING): forbid selecting it in prod.
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    r = await client.put(
        "/admin/settings/general",
        json={"payment_provider": "cinetpay", "site_url": "http://x"},
        headers=_basic(),
    )
    assert r.status_code == 422, r.text
    assert "CinetPay" in r.json()["detail"]


@pytest.mark.asyncio
async def test_cinetpay_allowed_outside_production(client, db_session_factory, monkeypatch):
    # dev/staging may select it to exercise the wiring.
    monkeypatch.setattr(settings, "ENVIRONMENT", "dev")
    r = await client.put(
        "/admin/settings/general",
        json={"payment_provider": "cinetpay", "site_url": "http://x"},
        headers=_basic(),
    )
    assert r.status_code == 200, r.text
    assert r.json()["values"]["payment_provider"] == "cinetpay"


@pytest.mark.asyncio
async def test_smtp_test_sends_via_injected_sender(client, db_session_factory, monkeypatch):
    sent = {}

    def fake_sender(msg, host, port, user, password):
        sent["host"] = host
        sent["to"] = msg["To"]

    import src.infrastructure.http.deps as deps

    monkeypatch.setattr(deps, "_default_send_smtp_message", fake_sender)

    await client.put(
        "/admin/settings/smtp",
        json={"host": "smtp.x", "user": "u", "password": "p", "from_email": "from@x"},
        headers=_basic(),
    )
    r = await client.post("/admin/settings/smtp/test", json={"to": "dest@x"}, headers=_basic())
    assert r.status_code == 204, r.text
    assert sent == {"host": "smtp.x", "to": "dest@x"}


@pytest.mark.asyncio
async def test_smtp_test_without_config_returns_400(client, db_session_factory):
    r = await client.post("/admin/settings/smtp/test", json={"to": "dest@x"}, headers=_basic())
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_sms_test_noop_when_unconfigured(client, db_session_factory):
    # No SMS provider configured → NoOpSms → endpoint succeeds (message dropped).
    r = await client.post("/admin/settings/sms/test", json={"to": "+22500000000"}, headers=_basic())
    assert r.status_code == 204, r.text
