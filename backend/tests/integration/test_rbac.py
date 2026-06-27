"""
RBAC matrix verified end-to-end.

The mapping ``Role → frozenset[Permission]`` lives in
:py:mod:`src.domain.role`; here we exercise it through the live FastAPI
app so the route-level ``Depends(require_permission(P))`` declarations
are part of the contract.
"""

from __future__ import annotations

import base64

import pytest


def _basic(username: str = "admin", password: str = "admin") -> dict:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


async def _create_operator_user(client, db_session_factory, *, username: str, role: str) -> str:
    """Returns the cookie-bearing client after the user logged in."""
    r = await client.post(
        "/admin/users",
        json={"username": username, "password": "longpassword", "role": role},
        headers=_basic(),
    )
    assert r.status_code == 201, r.text
    client.cookies.clear()  # drop the super-admin session if any
    r2 = await client.post("/auth/login", json={"username": username, "password": "longpassword"})
    assert r2.status_code == 200, r2.text
    return r2.json()["role"]


# --- super-admin: all permissions -------------------------------------------


@pytest.mark.asyncio
async def test_super_admin_can_delete_users(client, db_session_factory):
    # super-admin creates an operator
    r = await client.post(
        "/admin/users",
        json={"username": "to-delete", "password": "longpassword", "role": "operator"},
        headers=_basic(),
    )
    user_id = r.json()["id"]
    r2 = await client.delete(f"/admin/users/{user_id}", headers=_basic())
    assert r2.status_code == 204


# --- admin: everything but delete user --------------------------------------


@pytest.mark.asyncio
async def test_admin_can_create_users_but_not_delete(client, db_session_factory):
    # super-admin spawns an admin user
    role = await _create_operator_user(client, db_session_factory, username="alice", role="admin")
    assert role == "admin"

    # alice (admin) creates an operator
    r = await client.post(
        "/admin/users",
        json={"username": "newop", "password": "longpassword", "role": "operator"},
    )
    assert r.status_code == 201, r.text
    new_id = r.json()["id"]

    # alice tries to delete newop → 403, DELETE_USER is SA-only
    r2 = await client.delete(f"/admin/users/{new_id}")
    assert r2.status_code == 403, r2.text
    assert "delete:user" in r2.json()["detail"]


# --- operator: read + resend + export ---------------------------------------


@pytest.mark.asyncio
async def test_operator_can_read_stats_but_cannot_sync_payment(client, db_session_factory):
    await _create_operator_user(client, db_session_factory, username="ops", role="operator")

    # READ_STATS allowed
    r = await client.get("/admin/dashboard/stats")
    assert r.status_code == 200, r.text

    # SYNC_PAYMENT denied
    r2 = await client.post(
        "/admin/transactions/whatever/sync",
        json={"provider_tx_id": "kkia_x"},
    )
    assert r2.status_code == 403, r2.text
    assert "sync:payment" in r2.json()["detail"]


@pytest.mark.asyncio
async def test_operator_cannot_manage_users(client, db_session_factory):
    await _create_operator_user(client, db_session_factory, username="ops", role="operator")

    r = await client.get("/admin/users")
    assert r.status_code == 403, r.text
    assert "list:users" in r.json()["detail"]

    r2 = await client.post(
        "/admin/users",
        json={"username": "nope", "password": "longpassword", "role": "reader"},
    )
    assert r2.status_code == 403


# --- reader: stats + transactions list only ---------------------------------


@pytest.mark.asyncio
async def test_reader_can_only_read_transactions_and_stats(client, db_session_factory):
    await _create_operator_user(client, db_session_factory, username="reader1", role="reader")

    r = await client.get("/admin/transactions")
    assert r.status_code == 200

    r2 = await client.get("/admin/dashboard/stats")
    assert r2.status_code == 200

    # No export
    r3 = await client.get("/admin/transactions/export.xlsx")
    assert r3.status_code == 403

    # No resend
    r4 = await client.post("/admin/transactions/whatever/resend")
    assert r4.status_code == 403


# --- super_admin role cannot be assigned via CRUD ---------------------------


@pytest.mark.asyncio
async def test_cannot_create_user_with_super_admin_role(client, db_session_factory):
    r = await client.post(
        "/admin/users",
        json={"username": "shadow_sa", "password": "longpassword", "role": "super_admin"},
        headers=_basic(),
    )
    assert r.status_code == 400, r.text
    assert "super_admin" in r.json()["detail"]


@pytest.mark.asyncio
async def test_cannot_promote_user_to_super_admin(client, db_session_factory):
    r = await client.post(
        "/admin/users",
        json={"username": "innocent", "password": "longpassword", "role": "reader"},
        headers=_basic(),
    )
    user_id = r.json()["id"]

    r2 = await client.patch(
        f"/admin/users/{user_id}",
        json={"role": "super_admin"},
        headers=_basic(),
    )
    assert r2.status_code == 400


# --- unauthenticated: 401, not 403 ------------------------------------------


@pytest.mark.asyncio
async def test_unauthenticated_request_gets_401_not_403(client, db_session_factory):
    """We want WWW-Authenticate sent on 401, browsers/clients then know to
    initiate the auth flow. 403 is for authenticated-but-forbidden."""
    r = await client.get("/admin/dashboard/stats")
    assert r.status_code == 401
    assert "WWW-Authenticate" in r.headers
