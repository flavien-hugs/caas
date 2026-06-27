"""
Admin actions end-to-end:
- POST /v2/admin/transactions/{id}/resend
- POST /v2/admin/transactions/{id}/sync (security: amount validation)
- GET  /v2/admin/transactions/export.xlsx
"""

from __future__ import annotations

import base64
import zipfile
from io import BytesIO

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


# --- Resend ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resend_rejects_non_success_purchases(client, db_session_factory):
    pid = await _seed(db_session_factory, status="PENDING")
    r = await client.post(f"/admin/transactions/{pid}/resend", headers=_admin_headers())
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_resend_returns_404_for_unknown(client, db_session_factory):
    r = await client.post("/admin/transactions/does-not-exist/resend", headers=_admin_headers())
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_resend_calls_notification_for_success(client, db_session_factory):
    pid = await _seed(db_session_factory, status="SUCCESS")
    # Default test settings have empty SMTP_HOST → notification is NoOp, no error.
    r = await client.post(f"/admin/transactions/{pid}/resend", headers=_admin_headers())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["purchase_id"] == pid
    assert body["delivered"] is True


# --- Admin sync (manual confirm — security guard) ----------------------------


@pytest.mark.asyncio
async def test_admin_sync_amount_mismatch_blocks_with_security_error(client, db_session_factory, monkeypatch):
    """The critical regression test: legacy /sync-payment did not validate
    the paid amount (security review vuln #3). v2 MUST refuse to confirm a
    paid amount that differs from the expected one."""
    pid = await _seed(db_session_factory, amount=20_000.0)

    async def fake_verify(self, provider_tx_id: str) -> dict:
        return {"status": "SUCCESS", "amount": 1}  # mismatch

    from src.infrastructure.payment.kkiapay import KkiapayProvider

    monkeypatch.setattr(KkiapayProvider, "verify_payment", fake_verify)

    r = await client.post(
        f"/admin/transactions/{pid}/sync",
        json={"provider_tx_id": "kkia_BAD"},
        headers=_admin_headers(),
    )
    assert r.status_code == 200, r.text
    assert r.json()["confirmed"] is False

    # And the row must carry the security_error flag.
    async with db_session_factory() as session:
        row = await session.get(TransactionRow, pid)
    assert row.status == "FAILED"
    assert row.payment_metadata["security_error"] == "amount_mismatch"


@pytest.mark.asyncio
async def test_admin_sync_rejects_already_linked_provider_id(client, db_session_factory, monkeypatch):
    await _seed(db_session_factory, transaction_id="kkia_USED")
    b = await _seed(db_session_factory)

    r = await client.post(
        f"/admin/transactions/{b}/sync",
        json={"provider_tx_id": "kkia_USED"},
        headers=_admin_headers(),
    )
    assert r.status_code == 409, r.text


# --- Excel export ------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_xlsx_returns_valid_workbook(client, db_session_factory):
    await _seed(db_session_factory, status="SUCCESS", amount=20_000.0)
    await _seed(db_session_factory, status="PENDING", amount=10_000.0)

    r = await client.get("/admin/transactions/export.xlsx", headers=_admin_headers())
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    # An xlsx is a zip — verifying that proves the bytes are a real workbook.
    payload = r.read() if hasattr(r, "read") else r.content
    with zipfile.ZipFile(BytesIO(payload)) as zf:
        assert "xl/workbook.xml" in zf.namelist()
