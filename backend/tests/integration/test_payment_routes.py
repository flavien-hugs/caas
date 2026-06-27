"""
Integration tests for the new payment routes.

Exercises the full FastAPI stack with SQLite in-memory:
- POST /v2/payment/beacon
- GET  /v2/payment/callback (Kkiapay provider verify_payment is monkey-patched
  to a deterministic response — no network)
- GET  /v2/purchases/{id}
"""

from __future__ import annotations

import pytest

from src.infrastructure.persistence.models import TransactionRow


async def _seed_pending(db_session_factory, *, amount: float = 20_000.0, book_id: str = "lutte-contre-fraude") -> str:
    """Seed a PENDING row directly via the test DB factory."""
    async with db_session_factory() as session:  # type: AsyncSession
        row = TransactionRow(
            user_email="c@example.com",
            user_name="Candidate Test",
            book_id=book_id,
            amount=amount,
            status="PENDING",
        )
        session.add(row)
        await session.commit()
        return row.id


@pytest.mark.asyncio
async def test_get_purchase_returns_404_for_unknown(client):
    r = await client.get("/purchases/does-not-exist")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_purchase_returns_projection(client, db_session_factory):
    purchase_id = await _seed_pending(db_session_factory)
    r = await client.get(f"/purchases/{purchase_id}")
    assert r.status_code == 200
    body = r.json()
    assert body == {
        "id": purchase_id,
        "book_id": "lutte-contre-fraude",
        "status": "PENDING",
        "amount": 20_000,
        "currency": "XOF",
    }


@pytest.mark.asyncio
async def test_beacon_links_provider_tx_id(client, db_session_factory):
    purchase_id = await _seed_pending(db_session_factory)

    r = await client.post(
        "/payment/beacon",
        json={"internal_tx_id": purchase_id, "transaction_id": "kkia_xyz"},
    )
    assert r.status_code == 204

    async with db_session_factory() as session:
        row = await session.get(TransactionRow, purchase_id)
    assert row is not None
    assert row.transaction_id == "kkia_xyz"
    assert row.payment_metadata["beacon_transaction_id"] == "kkia_xyz"


@pytest.mark.asyncio
async def test_beacon_does_not_overwrite_existing_link(client, db_session_factory):
    purchase_id = await _seed_pending(db_session_factory)
    # Pre-link with a real Kkiapay id
    async with db_session_factory() as session:
        row = await session.get(TransactionRow, purchase_id)
        row.transaction_id = "kkia_original"
        session.add(row)
        await session.commit()

    r = await client.post(
        "/payment/beacon",
        json={"internal_tx_id": purchase_id, "transaction_id": "kkia_attacker"},
    )
    assert r.status_code == 204
    async with db_session_factory() as session:
        row = await session.get(TransactionRow, purchase_id)
    assert row.transaction_id == "kkia_original"


@pytest.mark.asyncio
async def test_callback_confirms_success_when_amounts_match(client, db_session_factory, monkeypatch):
    purchase_id = await _seed_pending(db_session_factory, amount=20_000.0)

    async def fake_verify(self, provider_tx_id: str) -> dict:
        return {"status": "SUCCESS", "amount": 20_000, "transactionId": provider_tx_id}

    from src.infrastructure.payment.kkiapay import KkiapayProvider

    monkeypatch.setattr(KkiapayProvider, "verify_payment", fake_verify)

    r = await client.get(f"/payment/callback?internal_tx_id={purchase_id}&transaction_id=kkia_OK")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["confirmed"] is True
    assert body["status"] == "SUCCESS"
    # Fraude product => WhatsApp delivery, not email
    assert body["delivered"] is False

    async with db_session_factory() as session:
        row = await session.get(TransactionRow, purchase_id)
    assert row.status == "SUCCESS"
    assert row.transaction_id == "kkia_OK"


@pytest.mark.asyncio
async def test_callback_blocks_amount_mismatch_with_security_error(client, db_session_factory, monkeypatch):
    purchase_id = await _seed_pending(db_session_factory, amount=20_000.0)

    async def fake_verify(self, provider_tx_id: str) -> dict:
        return {"status": "SUCCESS", "amount": 1, "transactionId": provider_tx_id}

    from src.infrastructure.payment.kkiapay import KkiapayProvider

    monkeypatch.setattr(KkiapayProvider, "verify_payment", fake_verify)

    r = await client.get(f"/payment/callback?internal_tx_id={purchase_id}&transaction_id=kkia_BAD")
    body = r.json()
    assert body["confirmed"] is False

    async with db_session_factory() as session:
        row = await session.get(TransactionRow, purchase_id)
    assert row.status == "FAILED"
    assert row.payment_metadata["security_error"] == "amount_mismatch"
