"""
Lock the Alembic chain in CI.

Two checks:

1. ``alembic upgrade head`` against a fresh in-memory SQLite must run the
   full chain without errors.

2. After the migrations land, the resulting schema must accept inserts via
   the SQLModel rows used by :class:`SqlPurchaseRepository`. If a future
   migration drifts from the model definitions, this round-trip explodes
   loudly instead of silently breaking prod sync at runtime.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlmodel import Session

from alembic import command
from src.infrastructure.persistence.models import FeedbackRow, TransactionRow


@pytest.fixture
def alembic_cfg_with_temp_db():
    """Apply migrations against a throwaway SQLite file and yield its URL."""
    backend_root = Path(__file__).resolve().parents[2]  # backend/
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    # Sync driver here — Alembic runs sync, env.py strips the +aiosqlite/+asyncpg suffix.
    url = f"sqlite+aiosqlite:///{db_path}"
    prev = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    # Rebuild settings instance so env.py picks up our override.
    from src.infrastructure.config import settings as settings_mod

    settings_mod.get_settings.cache_clear()  # type: ignore[attr-defined]
    settings_mod.settings = settings_mod.get_settings()

    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    try:
        yield cfg, f"sqlite:///{db_path}"
    finally:
        if prev is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev
        settings_mod.get_settings.cache_clear()  # type: ignore[attr-defined]
        settings_mod.settings = settings_mod.get_settings()
        Path(db_path).unlink(missing_ok=True)


def test_alembic_upgrade_head_creates_expected_tables(alembic_cfg_with_temp_db):
    cfg, sync_url = alembic_cfg_with_temp_db
    command.upgrade(cfg, "head")

    engine = create_engine(sync_url)
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert "transactions" in tables
    assert "feedbacks" in tables
    assert "alembic_version" in tables

    # Critical columns + indexes the rest of the app relies on.
    tx_cols = {c["name"] for c in insp.get_columns("transactions")}
    assert {
        "id",
        "user_email",
        "amount",
        "status",
        "book_id",
        "transaction_id",
        "payment_metadata",
        "client_metadata",
        "created_at",
    }.issubset(tx_cols)

    tx_indexes = {idx["name"] for idx in insp.get_indexes("transactions")}
    # Indexes actually produced by the legacy migration chain. Note that
    # the SQLModel declares ``status`` and ``created_at`` with ``index=True``
    # but the prod migrations never created those indexes — a known drift
    # to fix in a follow-up migration (additive, non-breaking).
    assert "ix_transactions_book_id" in tx_indexes
    assert "ix_transactions_transaction_id" in tx_indexes


def test_sqlmodel_rows_round_trip_against_migrated_schema(alembic_cfg_with_temp_db):
    """Insert + read through the SQLModel rows to prove model ↔ schema parity."""
    cfg, sync_url = alembic_cfg_with_temp_db
    command.upgrade(cfg, "head")

    engine = create_engine(sync_url)
    with Session(engine) as session:
        tx = TransactionRow(
            user_email="x@y.z",
            user_name="Buyer",
            book_id="lutte-contre-fraude",
            amount=20_000.0,
            status="PENDING",
        )
        fb = FeedbackRow(user_name="Buyer", rating=5, message="great")
        session.add(tx)
        session.add(fb)
        session.commit()
        session.refresh(tx)
        session.refresh(fb)

    assert tx.id and fb.id
    assert tx.status == "PENDING"
    assert fb.rating == 5
