"""
End-to-end reconciliation: seed PENDING rows directly in SQLite (mimicking
purchases initiated by the legacy ``app/`` monolith), run the real
ReconcilePending wired via the composition root, and assert the rows
transition correctly.

This is the test that proves the strangler-fig step actually works:
``backend/`` reads rows written by ``app/`` and finalizes them without any
schema change.
"""

from __future__ import annotations

import pytest

from src.application.use_cases import ReconcilePendingInput
from src.infrastructure.http.deps import build_reconcile_pending, build_resolved_config
from src.infrastructure.persistence.models import TransactionRow


async def _seed(session_factory, **fields) -> str:
    defaults = {
        "user_email": "c@example.com",
        "user_name": "Candidate",
        "book_id": "lutte-contre-fraude",
        "amount": 20_000.0,
        "status": "PENDING",
    }
    defaults.update(fields)
    async with session_factory() as session:
        row = TransactionRow(**defaults)
        session.add(row)
        await session.commit()
        return row.id


@pytest.mark.asyncio
async def test_reconcile_confirms_success_and_blocks_mismatch(db_session_factory, monkeypatch):
    # Three rows seeded:
    #   - row_ok: has provider_tx_id, provider will return SUCCESS at the right amount
    #   - row_bad: has provider_tx_id, provider will return SUCCESS at a wrong amount → security_error
    #   - row_orphan: no provider_tx_id, no metadata fallback → skipped
    row_ok = await _seed(db_session_factory, transaction_id="kkia_OK")
    row_bad = await _seed(db_session_factory, transaction_id="kkia_BAD")
    row_orphan = await _seed(db_session_factory)

    async def fake_verify(self, provider_tx_id: str) -> dict:
        if provider_tx_id == "kkia_OK":
            return {"status": "SUCCESS", "amount": 20_000}
        return {"status": "SUCCESS", "amount": 1}  # mismatch

    from src.infrastructure.payment.kkiapay import KkiapayProvider

    monkeypatch.setattr(KkiapayProvider, "verify_payment", fake_verify)

    cfg = await build_resolved_config()
    summary = await build_reconcile_pending(cfg).execute(ReconcilePendingInput())

    assert summary.processed == 3
    assert summary.confirmed == 1
    assert summary.failed == 1  # the amount-mismatch row
    assert summary.skipped == 1  # the orphan
    assert summary.purchase_ids_confirmed == [row_ok]

    async with db_session_factory() as session:
        ok = await session.get(TransactionRow, row_ok)
        bad = await session.get(TransactionRow, row_bad)
        orphan = await session.get(TransactionRow, row_orphan)

    assert ok.status == "SUCCESS"
    assert bad.status == "FAILED"
    assert bad.payment_metadata["security_error"] == "amount_mismatch"
    assert orphan.status == "PENDING"  # untouched


@pytest.mark.asyncio
async def test_reconcile_respects_book_id_filter(db_session_factory, monkeypatch):
    fraude_id = await _seed(db_session_factory, transaction_id="kkia_F", book_id="lutte-contre-fraude")
    africa_id = await _seed(db_session_factory, transaction_id="kkia_A", book_id="sbbs-africa-1")

    async def fake_verify(self, provider_tx_id: str) -> dict:
        return {"status": "SUCCESS", "amount": 20_000}

    from src.infrastructure.payment.kkiapay import KkiapayProvider

    monkeypatch.setattr(KkiapayProvider, "verify_payment", fake_verify)

    cfg = await build_resolved_config()
    summary = await build_reconcile_pending(cfg).execute(ReconcilePendingInput(book_ids=["lutte-contre-fraude"]))

    assert summary.processed == 1
    assert summary.confirmed == 1
    assert summary.purchase_ids_confirmed == [fraude_id]

    # The africa row was filtered out at the SQL level — still PENDING.
    async with db_session_factory() as session:
        africa = await session.get(TransactionRow, africa_id)
    assert africa.status == "PENDING"
