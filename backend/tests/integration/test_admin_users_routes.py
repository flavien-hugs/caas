"""
Operator user CRUD + the two-layer login (super-admin env, operator DB).

Critical invariants verified:

- The super-admin (env-keyed admin/admin) NEVER shows up in
  GET /admin/users — it's not in the ``users`` table by design.
- Operator users created via POST /admin/users can log in with their own
  password (bcrypted in storage).
- Username uniqueness is enforced at create AND update.
"""

from __future__ import annotations

import base64

import pytest


def _basic(username: str = "admin", password: str = "admin") -> dict:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.mark.asyncio
async def test_super_admin_is_not_in_users_list(client, db_session_factory):
    """Super-admin login works (env), but the users list is empty until an
    operator is created — the super-admin is structurally absent."""
    r = await client.get("/admin/users", headers=_basic())
    assert r.status_code == 200, r.text
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_operator_user_and_list_contains_only_it(client, db_session_factory):
    r = await client.post(
        "/admin/users",
        json={"username": "alice", "password": "longpassword", "role": "operator"},
        headers=_basic(),
    )
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["username"] == "alice"
    assert created["role"] == "operator"
    assert "password" not in created and "password_hash" not in created

    r2 = await client.get("/admin/users", headers=_basic())
    assert r2.status_code == 200
    listing = r2.json()
    # Exactly one row — the operator — super-admin is still NOT here
    assert len(listing) == 1
    assert listing[0]["username"] == "alice"


@pytest.mark.asyncio
async def test_create_user_username_unique(client, db_session_factory):
    payload = {"username": "alice", "password": "longpassword", "role": "operator"}
    await client.post("/admin/users", json=payload, headers=_basic())

    r = await client.post("/admin/users", json=payload, headers=_basic())
    assert r.status_code == 409, r.text


@pytest.mark.asyncio
async def test_get_user_404_when_unknown(client, db_session_factory):
    r = await client.get("/admin/users/does-not-exist", headers=_basic())
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_user_password_changes_login_outcome(client, db_session_factory):
    # Create operator
    r = await client.post(
        "/admin/users",
        json={"username": "bob", "password": "initial_password", "role": "operator"},
        headers=_basic(),
    )
    user_id = r.json()["id"]

    # Login with the original password
    r1 = await client.post("/auth/login", json={"username": "bob", "password": "initial_password"})
    assert r1.status_code == 200, r1.text

    # Bob is OPERATOR — wouldn't have UPDATE_USER. Super-admin patches the
    # password; we drop bob's session cookie first so require_admin falls
    # back to the Basic Auth header.
    client.cookies.clear()

    r2 = await client.patch(
        f"/admin/users/{user_id}",
        json={"password": "new_password_xyz"},
        headers=_basic(),
    )
    assert r2.status_code == 200, r2.text

    # Old password rejected
    r3 = await client.post("/auth/login", json={"username": "bob", "password": "initial_password"})
    assert r3.status_code == 401
    # New password accepted
    r4 = await client.post("/auth/login", json={"username": "bob", "password": "new_password_xyz"})
    assert r4.status_code == 200


@pytest.mark.asyncio
async def test_update_user_username_conflict_returns_409(client, db_session_factory):
    await client.post(
        "/admin/users", json={"username": "alice", "password": "longpassword", "role": "operator"}, headers=_basic()
    )
    r = await client.post(
        "/admin/users", json={"username": "bob", "password": "longpassword", "role": "operator"}, headers=_basic()
    )
    bob_id = r.json()["id"]

    r2 = await client.patch(f"/admin/users/{bob_id}", json={"username": "alice"}, headers=_basic())
    assert r2.status_code == 409, r2.text


@pytest.mark.asyncio
async def test_delete_user_removes_it_and_blocks_login(client, db_session_factory):
    r = await client.post(
        "/admin/users",
        json={"username": "charlie", "password": "longpassword", "role": "operator"},
        headers=_basic(),
    )
    user_id = r.json()["id"]

    r2 = await client.delete(f"/admin/users/{user_id}", headers=_basic())
    assert r2.status_code == 204

    # Login no longer works
    r3 = await client.post("/auth/login", json={"username": "charlie", "password": "longpassword"})
    assert r3.status_code == 401

    # And the list is empty again — super-admin still not there
    r4 = await client.get("/admin/users", headers=_basic())
    assert r4.json() == []


@pytest.mark.asyncio
async def test_routes_require_admin(client, db_session_factory):
    r = await client.get("/admin/users")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_operator_can_login_and_hit_admin_routes(client, db_session_factory):
    """End-to-end: super-admin creates an operator, operator logs in via
    cookie, then uses the cookie to reach an admin route."""
    await client.post(
        "/admin/users",
        json={"username": "ops", "password": "ops_password", "role": "operator"},
        headers=_basic(),
    )

    r = await client.post("/auth/login", json={"username": "ops", "password": "ops_password"})
    assert r.status_code == 200, r.text
    # The cookie is now attached to the test client's session
    r2 = await client.get("/admin/dashboard/stats")
    assert r2.status_code == 200, r2.text
