"""
Admin dashboard read endpoints (transactions list, stats, revenue chart).

Auth is HTTP Basic with admin/admin (default settings). Auth failure is
verified on one route; the rest use the auth header to focus on payload.
"""

from __future__ import annotations

import base64

import pytest

from src.infrastructure.persistence.models import TransactionRow


def _admin_headers() -> dict:
    token = base64.b64encode(b"admin:admin").decode()
    return {"Authorization": f"Basic {token}"}


async def _seed(session_factory, **fields) -> str:
    defaults = {
        "user_email": "c@example.com",
        "user_name": "Candidate",
        "user_phone": "+225",
        "user_country": "CI",
        "user_city": "Abidjan",
        "book_id": "lutte-contre-fraude",
        "amount": 20_000.0,
        "status": "PENDING",
    }
    defaults.update(fields)
    async with session_factory() as session:  # type: AsyncSession
        row = TransactionRow(**defaults)
        session.add(row)
        await session.commit()
        return row.id


@pytest.mark.asyncio
async def test_admin_routes_require_basic_auth(client, db_session_factory):
    r = await client.get("/admin/transactions")
    assert r.status_code == 401
    assert "WWW-Authenticate" in r.headers


@pytest.mark.asyncio
async def test_list_transactions_paginated_with_filters(client, db_session_factory):
    success_id = await _seed(db_session_factory, status="SUCCESS", amount=20_000.0)
    await _seed(db_session_factory, status="PENDING", amount=15_000.0, user_email="other@x.z")
    await _seed(db_session_factory, status="FAILED", amount=1_000.0, book_id="multi-business")

    r = await client.get(
        "/admin/transactions?size=10&page=1&status=SUCCESS",
        headers=_admin_headers(),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 1
    assert body["size"] == 10
    assert body["pages"] == 1
    [item] = body["items"]
    assert item["id"] == success_id
    assert item["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_dashboard_stats_aggregates_correctly(client, db_session_factory):
    await _seed(db_session_factory, status="SUCCESS", amount=20_000.0)
    await _seed(db_session_factory, status="SUCCESS", amount=10_000.0)
    await _seed(db_session_factory, status="PENDING", amount=5_000.0)
    await _seed(db_session_factory, status="FAILED", amount=7_000.0)

    r = await client.get("/admin/dashboard/stats", headers=_admin_headers())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_revenue"] == 30_000.0
    assert body["successful_sales"] == 2
    assert body["pending_transactions"] == 1
    assert body["failed_transactions"] == 1
    assert body["total_transactions"] == 4


@pytest.mark.asyncio
async def test_revenue_chart_returns_daily_series(client, db_session_factory):
    await _seed(db_session_factory, status="SUCCESS", amount=12_000.0)
    r = await client.get("/admin/dashboard/revenue?days=7", headers=_admin_headers())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["days"] == 7
    # Today's revenue must be in there (SQLite's CURRENT_DATE matches our insert).
    total = sum(p["revenue"] for p in body["series"])
    assert total == 12_000.0
