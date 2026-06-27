"""
Integration tests for ``POST /v2/purchases``.

Hits the real FastAPI app, the real composition root, and a real SQLite DB.
The payment provider is left as KkiapayProvider which returns a deterministic
render URL without network calls — so we don't need to mock it here.
"""

from __future__ import annotations

import pytest
from sqlmodel import select

from src.infrastructure.config.settings import get_settings
from src.infrastructure.persistence import TransactionRow


@pytest.mark.asyncio
async def test_create_purchase_persists_pending_row(client, db_session_factory):
    payload = {
        "book_id": "lutte-contre-fraude",
        "email": "candidate@example.com",
        "name": "Candidate",
        "surname": "Test",
        "phone": "+225 07 00 00 00 00",
        "country": "Côte d'Ivoire",
        "city": "Abidjan",
    }

    r = await client.post("/purchases", json=payload)
    assert r.status_code == 201, r.text

    body = r.json()
    assert body["payment_url"].startswith("/v2/payment/render/")
    assert body["currency"] == "XOF"
    # Server-authoritative price — whatever the settings catalog says wins.
    assert body["amount"] == get_settings().FRAUDE_WEBINAIRE_PRICE

    async with db_session_factory() as session:  # type: AsyncSession
        rows = (await session.execute(select(TransactionRow))).scalars().all()
    assert len(rows) == 1
    row = rows[0]
    assert row.status == "PENDING"
    assert row.book_id == "lutte-contre-fraude"
    assert row.user_email == "candidate@example.com"
    assert row.user_name == "Candidate Test"
    assert row.payment_metadata["checkout_url"] == body["payment_url"]


@pytest.mark.asyncio
async def test_unknown_book_id_returns_404(client, db_session_factory):
    payload = {
        "book_id": "no-such-product",
        "email": "x@y.z",
        "name": "X",
        "surname": "Y",
        "phone": "+225",
        "country": "CI",
        "city": "Abidjan",
    }
    r = await client.post("/purchases", json=payload)
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_invalid_payload_returns_422(client, db_session_factory):
    # missing required fields → Pydantic returns 422
    r = await client.post("/purchases", json={"book_id": "lutte-contre-fraude"})
    assert r.status_code == 422
