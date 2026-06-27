"""
Page builder CRUD + publish/unpublish + public lookup invariants.

Critical contracts verified:

- Admin routes are guarded by MANAGE_PAGES: OPERATOR/READER get 403,
  even logged in.
- Slug is unique across pages (409 on conflict at create AND rename).
- Slugs are normalised: ``  My Page  `` → ``my-page``; malformed slugs
  return 422.
- Public ``GET /pages/{slug}`` returns the page only if PUBLISHED;
  DRAFTs return the same 404 as an unknown slug (no draft enumeration).
- Block payloads round-trip verbatim: backend stores ``props`` as opaque
  JSON, doesn't interpret block types.
"""

from __future__ import annotations

import base64
import uuid

import pytest


def _basic(username: str = "admin", password: str = "admin") -> dict:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.mark.asyncio
async def test_create_page_returns_201_with_normalized_slug_and_draft_status(client, db_session_factory):
    r = await client.post(
        "/admin/pages",
        json={"slug": "  My First Page  ", "title": "Première page"},
        headers=_basic(),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["slug"] == "my-first-page"
    assert body["title"] == "Première page"
    assert body["status"] == "draft"
    assert body["blocks"] == []
    assert body["published_at"] is None
    uuid.UUID(body["id"])  # well-formed uuid


@pytest.mark.asyncio
async def test_create_page_invalid_slug_returns_422(client, db_session_factory):
    r = await client.post(
        "/admin/pages",
        json={"slug": "!!!", "title": "Bad"},
        headers=_basic(),
    )
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_create_page_slug_already_taken_returns_409(client, db_session_factory):
    payload = {"slug": "twin", "title": "Twin"}
    await client.post("/admin/pages", json=payload, headers=_basic())
    r = await client.post("/admin/pages", json=payload, headers=_basic())
    assert r.status_code == 409, r.text


@pytest.mark.asyncio
async def test_update_page_blocks_roundtrip_verbatim(client, db_session_factory):
    r = await client.post(
        "/admin/pages",
        json={"slug": "blocks-test", "title": "Blocks"},
        headers=_basic(),
    )
    page_id = r.json()["id"]

    blocks = [
        {"id": "b1", "type": "hero", "props": {"headline": "Hi", "background": "dark"}},
        {"id": "b2", "type": "cta_button", "props": {"label": "Go", "href": "https://x"}},
        {"id": "b3", "type": "rich_text", "props": {"html": "<p>nested</p>", "meta": {"k": 1}}},
    ]
    r2 = await client.patch(f"/admin/pages/{page_id}", json={"blocks": blocks}, headers=_basic())
    assert r2.status_code == 200, r2.text
    assert r2.json()["blocks"] == blocks


@pytest.mark.asyncio
async def test_update_page_rename_slug_conflict_returns_409(client, db_session_factory):
    await client.post("/admin/pages", json={"slug": "alpha", "title": "A"}, headers=_basic())
    r = await client.post("/admin/pages", json={"slug": "beta", "title": "B"}, headers=_basic())
    beta_id = r.json()["id"]

    r2 = await client.patch(f"/admin/pages/{beta_id}", json={"slug": "alpha"}, headers=_basic())
    assert r2.status_code == 409, r2.text


@pytest.mark.asyncio
async def test_publish_then_unpublish_flips_status_and_published_at(client, db_session_factory):
    r = await client.post(
        "/admin/pages",
        json={"slug": "lifecycle", "title": "Lifecycle"},
        headers=_basic(),
    )
    page_id = r.json()["id"]

    rp = await client.post(f"/admin/pages/{page_id}/publish", headers=_basic())
    assert rp.status_code == 200, rp.text
    pb = rp.json()
    assert pb["status"] == "published"
    assert pb["published_at"] is not None

    ru = await client.post(f"/admin/pages/{page_id}/unpublish", headers=_basic())
    assert ru.status_code == 200
    assert ru.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_public_route_returns_404_for_draft_and_unknown(client, db_session_factory):
    # Existing draft
    await client.post(
        "/admin/pages",
        json={"slug": "hidden", "title": "Hidden"},
        headers=_basic(),
    )
    r = await client.get("/pages/hidden")
    assert r.status_code == 404

    # Unknown slug
    r2 = await client.get("/pages/does-not-exist")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_public_route_returns_page_only_when_published(client, db_session_factory):
    r = await client.post(
        "/admin/pages",
        json={"slug": "vitrine", "title": "Vitrine"},
        headers=_basic(),
    )
    page_id = r.json()["id"]
    await client.patch(
        f"/admin/pages/{page_id}",
        json={"blocks": [{"id": "h1", "type": "hero", "props": {"headline": "Bonjour"}}]},
        headers=_basic(),
    )
    await client.post(f"/admin/pages/{page_id}/publish", headers=_basic())

    r2 = await client.get("/pages/vitrine")
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["slug"] == "vitrine"
    assert body["title"] == "Vitrine"
    assert body["blocks"][0]["props"]["headline"] == "Bonjour"
    assert "status" not in body  # public schema omits status


@pytest.mark.asyncio
async def test_delete_page_removes_it(client, db_session_factory):
    r = await client.post(
        "/admin/pages",
        json={"slug": "ephemere", "title": "Éphémère"},
        headers=_basic(),
    )
    page_id = r.json()["id"]

    rd = await client.delete(f"/admin/pages/{page_id}", headers=_basic())
    assert rd.status_code == 204

    rg = await client.get(f"/admin/pages/{page_id}", headers=_basic())
    assert rg.status_code == 404


@pytest.mark.asyncio
async def test_admin_routes_require_auth_and_manage_pages_permission(client, db_session_factory):
    # Unauthenticated → 401
    r = await client.get("/admin/pages")
    assert r.status_code == 401

    # Operator logs in → MANAGE_PAGES not in ROLE_PERMISSIONS[OPERATOR] → 403
    await client.post(
        "/admin/users",
        json={"username": "opa", "password": "opa_password", "role": "operator"},
        headers=_basic(),
    )
    rlogin = await client.post("/auth/login", json={"username": "opa", "password": "opa_password"})
    assert rlogin.status_code == 200

    r2 = await client.get("/admin/pages")
    assert r2.status_code == 403, r2.text
