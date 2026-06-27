"""
Authentication flow:
- POST /auth/login (bad/good credentials)
- POST /auth/logout
- GET  /auth/me
- Admin routes accept the session cookie AND keep accepting HTTP Basic.
"""

from __future__ import annotations

import base64

import pytest


def _basic_headers(username: str = "admin", password: str = "admin") -> dict:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.mark.asyncio
async def test_login_rejects_bad_credentials(client):
    r = await client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_sets_session_cookie(client):
    r = await client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["username"] == "admin"
    assert body["role"] == "super_admin"
    # SessionMiddleware sets the cookie via Set-Cookie
    set_cookies = r.headers.get_list("set-cookie") if hasattr(r.headers, "get_list") else [r.headers.get("set-cookie", "")]
    cookie_blob = " ".join(set_cookies)
    assert "caas_session" in cookie_blob


@pytest.mark.asyncio
async def test_me_requires_session(client):
    r = await client.get("/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_then_me_returns_username(client):
    r = await client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert r.status_code == 200
    r2 = await client.get("/auth/me")
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["username"] == "admin"
    assert body["role"] == "super_admin"


@pytest.mark.asyncio
async def test_logout_clears_session(client):
    await client.post("/auth/login", json={"username": "admin", "password": "admin"})
    r = await client.post("/auth/logout")
    assert r.status_code == 204
    r2 = await client.get("/auth/me")
    assert r2.status_code == 401


# --- Admin route auth: both transports must work -----------------------------


@pytest.mark.asyncio
async def test_admin_route_accepts_session_cookie(client, db_session_factory):
    # Login first to plant the cookie
    r = await client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert r.status_code == 200
    # Now hit an admin route WITHOUT Authorization header
    r2 = await client.get("/admin/dashboard/stats")
    assert r2.status_code == 200, r2.text


@pytest.mark.asyncio
async def test_admin_route_keeps_accepting_http_basic(client, db_session_factory):
    """Legacy callers (curl, scripts, CI tests) keep working without
    going through the login flow."""
    r = await client.get("/admin/dashboard/stats", headers=_basic_headers())
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_admin_route_rejects_bad_basic(client):
    r = await client.get("/admin/dashboard/stats", headers=_basic_headers(password="wrong"))
    assert r.status_code == 401
