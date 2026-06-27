"""
SQLModel rows mapping the existing ``transactions`` schema 1:1.

Phase 1 cohabits with the legacy ``app/`` on the same Postgres DB and the same
table, so this definition must stay byte-identical to ``app/models.py``. Any
schema evolution is additive-only (new nullable columns), introduced through
the backend Alembic migrations.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlmodel import JSON, Column, Field, SQLModel, Text


class UserRow(SQLModel, table=True):
    """Operator users (DB). The super-admin (env-keyed) is intentionally NOT
    stored here — keeping the table purely operator-scoped means every CRUD
    response is correct by construction."""

    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(nullable=False, unique=True, index=True)
    password_hash: str = Field(nullable=False)
    # Role is persisted as its string value (StrEnum) for portability.
    # Default ``reader`` is the safest landing if anything corrupts the value.
    role: str = Field(default="reader", nullable=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackRow(SQLModel, table=True):
    """
    User feedback rows. Phase 1 doesn't yet expose endpoints to read/write
    these, but the table must exist on SQLModel.metadata so the baseline
    Alembic migration creates it on a fresh DB and autogenerate doesn't
    later mark it for DROP on the shared prod DB.
    """

    __tablename__ = "feedbacks"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_name: str = Field(nullable=False)
    rating: int = Field(ge=1, le=5, index=True)
    message: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PageRow(SQLModel, table=True):
    """Builder-authored pages (CMS).

    ``blocks`` is a JSON array of ``{id, type, props}`` records. The backend
    stores it verbatim; per-type schema validation is owned by the frontend
    (Zod). This lets us add new block types without backend deploys.
    """

    __tablename__ = "pages"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    slug: str = Field(nullable=False, unique=True, index=True)
    title: str = Field(nullable=False)
    blocks: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    # ``status`` stored as the StrEnum value ("draft" | "published") for portability.
    status: str = Field(default="draft", nullable=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = Field(default=None)


class AppSettingRow(SQLModel, table=True):
    """Runtime configuration, one row per :class:`~src.domain.ConfigSection`.

    ``value`` is an opaque JSON blob; secret fields inside it are already
    encrypted by the application layer before they reach here. The resolver
    merges these rows over the env-keyed defaults.
    """

    __tablename__ = "app_settings"

    key: str = Field(primary_key=True)
    value: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionRow(SQLModel, table=True):
    __tablename__ = "transactions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_email: str = Field(nullable=False)
    user_name: Optional[str] = Field(default=None)
    user_phone: Optional[str] = Field(default=None)
    user_country: Optional[str] = Field(default=None)
    user_city: Optional[str] = Field(default=None)
    user_ip: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    book_id: Optional[str] = Field(default=None, index=True)
    client_metadata: Optional[dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    amount: float = Field(nullable=False)
    currency: str = Field(default="XOF")
    status: str = Field(default="PENDING", index=True)
    transaction_id: Optional[str] = Field(default=None, unique=True, index=True)
    payment_metadata: Optional[dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
