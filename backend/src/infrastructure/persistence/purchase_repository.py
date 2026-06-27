"""
SQL implementation of :class:`PurchaseRepositoryPort`.

Translates the Purchase aggregate (domain layer, pure dataclasses) to and from
:class:`TransactionRow` (SQLModel). The mapping is straightforward except for:

- the customer is flattened into the row's ``user_*`` columns (the legacy
  schema doesn't model a nested customer);
- ``payment_ref.provider`` is not persisted in phase 1 (the provider is a
  process-wide setting; phase 2 will move it onto the row to support
  per-tenant provider choice).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import AsyncIterator

from sqlalchemy import case, func, or_
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dashboard_filters import TransactionFilters
from src.application.ports.purchase_repository import (
    PaginatedPurchases,
    RevenuePoint,
    TransactionStats,
)
from src.domain import (
    Currency,
    Customer,
    Money,
    PaymentProviderName,
    PaymentReference,
    Purchase,
    PurchaseStatus,
)

from .models import TransactionRow


def _to_row(p: Purchase) -> TransactionRow:
    return TransactionRow(
        id=p.id,
        user_email=p.customer.email,
        user_name=p.customer.name,
        user_phone=p.customer.phone,
        user_country=p.customer.country,
        user_city=p.customer.city,
        user_ip=p.customer.ip,
        user_agent=p.customer.user_agent,
        latitude=p.customer.latitude,
        longitude=p.customer.longitude,
        book_id=p.book_id,
        client_metadata=dict(p.client_metadata),
        amount=float(p.amount.amount),
        currency=p.amount.currency.value,
        status=p.status.value,
        transaction_id=p.payment_ref.provider_tx_id,
        payment_metadata=dict(p.payment_metadata),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _to_domain(row: TransactionRow, provider: PaymentProviderName) -> Purchase:
    return Purchase(
        id=row.id,
        book_id=row.book_id or "",
        customer=Customer(
            email=row.user_email,
            name=row.user_name or "",
            phone=row.user_phone or "",
            country=row.user_country or "",
            city=row.user_city or "",
            ip=row.user_ip,
            user_agent=row.user_agent,
            latitude=row.latitude,
            longitude=row.longitude,
        ),
        amount=Money(amount=int(round(row.amount)), currency=Currency(row.currency)),
        status=PurchaseStatus(row.status),
        payment_ref=PaymentReference(provider=provider, provider_tx_id=row.transaction_id),
        client_metadata=dict(row.client_metadata or {}),
        payment_metadata=dict(row.payment_metadata or {}),
        created_at=row.created_at,
        updated_at=row.updated_at or row.created_at,
    )


class SqlPurchaseRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], provider: PaymentProviderName) -> None:
        self._sf = session_factory
        self._provider = provider

    async def add(self, purchase: Purchase) -> None:
        async with self._sf() as session:
            session.add(_to_row(purchase))
            await session.commit()

    async def get(self, purchase_id: str) -> Purchase | None:
        async with self._sf() as session:
            row = await session.get(TransactionRow, purchase_id)
            return _to_domain(row, self._provider) if row else None

    async def get_by_provider_tx_id(self, provider_tx_id: str) -> Purchase | None:
        async with self._sf() as session:
            stmt = select(TransactionRow).where(TransactionRow.transaction_id == provider_tx_id)
            row = (await session.execute(stmt)).scalars().first()
            return _to_domain(row, self._provider) if row else None

    async def save(self, purchase: Purchase) -> None:
        """Insert-or-update by primary key. Idempotent across replays."""
        async with self._sf() as session:
            row = await session.get(TransactionRow, purchase.id)
            new_values = _to_row(purchase)
            if row is None:
                session.add(new_values)
            else:
                for field, value in new_values.model_dump(exclude={"id"}).items():
                    setattr(row, field, value)
                session.add(row)
            await session.commit()

    async def list_pending(self, book_ids: list[str] | None = None) -> list[Purchase]:
        async with self._sf() as session:
            stmt = select(TransactionRow).where(TransactionRow.status.in_(["PENDING", "FAILED"]))
            if book_ids:
                stmt = stmt.where(TransactionRow.book_id.in_(book_ids))
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(r, self._provider) for r in rows]

    def _apply_filters(self, stmt, filters: TransactionFilters):
        """Common ``WHERE`` clause builder mirroring ``app/routers/admin._apply_filters``."""
        stmt = stmt.where(TransactionRow.amount >= filters.min_amount)
        if filters.q:
            term = f"%{filters.q}%"
            stmt = stmt.where(
                or_(
                    TransactionRow.user_email.ilike(term),
                    TransactionRow.user_name.ilike(term),
                    TransactionRow.user_phone.ilike(term),
                    TransactionRow.transaction_id.ilike(term),
                    TransactionRow.book_id.ilike(term),
                )
            )
        if filters.status:
            stmt = stmt.where(TransactionRow.status == filters.status)
        if filters.book_id:
            stmt = stmt.where(TransactionRow.book_id == filters.book_id)
        if filters.start_date:
            stmt = stmt.where(TransactionRow.created_at >= datetime.combine(filters.start_date, datetime.min.time()))
        if filters.end_date:
            stmt = stmt.where(TransactionRow.created_at <= datetime.combine(filters.end_date, datetime.max.time()))
        return stmt

    async def list_paginated(self, filters: TransactionFilters, page: int, size: int) -> PaginatedPurchases:
        page = max(1, page)
        size = max(1, min(size, 200))
        offset = (page - 1) * size

        async with self._sf() as session:
            total_stmt = self._apply_filters(select(func.count(TransactionRow.id)), filters)
            total = (await session.execute(total_stmt)).scalar_one()

            list_stmt = (
                self._apply_filters(select(TransactionRow), filters)
                .order_by(TransactionRow.created_at.desc())
                .offset(offset)
                .limit(size)
            )
            rows = (await session.execute(list_stmt)).scalars().all()

        return PaginatedPurchases(
            items=[_to_domain(r, self._provider) for r in rows],
            total=total,
            page=page,
            size=size,
        )

    async def compute_stats(self, filters: TransactionFilters) -> TransactionStats:
        async with self._sf() as session:
            stmt = self._apply_filters(
                select(
                    func.coalesce(
                        func.sum(case((TransactionRow.status == "SUCCESS", TransactionRow.amount), else_=0)),
                        0,
                    ).label("total_revenue"),
                    func.sum(case((TransactionRow.status == "SUCCESS", 1), else_=0)).label("successful_sales"),
                    func.sum(case((TransactionRow.status == "PENDING", 1), else_=0)).label("pending_transactions"),
                    func.sum(case((TransactionRow.status == "FAILED", 1), else_=0)).label("failed_transactions"),
                    func.count(TransactionRow.id).label("total_transactions"),
                ),
                filters,
            )
            row = (await session.execute(stmt)).one()

        return TransactionStats(
            total_revenue=float(row.total_revenue or 0),
            successful_sales=int(row.successful_sales or 0),
            pending_transactions=int(row.pending_transactions or 0),
            failed_transactions=int(row.failed_transactions or 0),
            total_transactions=int(row.total_transactions or 0),
        )

    async def revenue_last_days(self, filters: TransactionFilters, days: int) -> list[RevenuePoint]:
        """Aggregate SUCCESS revenue by day, in Python.

        The legacy code used ``cast(created_at, Date)`` directly in SQL, but
        SQLite's date coercion is fragile and breaks tests. For 30-day
        windows the row count is small enough that aggregating in Python is
        cheaper than the cross-driver gymnastics."""
        since = datetime.utcnow() - timedelta(days=days - 1)
        async with self._sf() as session:
            stmt = self._apply_filters(
                select(TransactionRow.created_at, TransactionRow.amount)
                .where(TransactionRow.status == "SUCCESS")
                .where(TransactionRow.created_at >= since),
                filters,
            )
            rows = (await session.execute(stmt)).all()

        buckets: dict = {}
        for created_at, amount in rows:
            day = created_at.date() if hasattr(created_at, "date") else created_at
            buckets[day] = buckets.get(day, 0.0) + float(amount)
        return [RevenuePoint(day=d, revenue=v) for d, v in sorted(buckets.items())]

    async def iter_for_export(self, filters: TransactionFilters) -> AsyncIterator[Purchase]:
        """Yields every matching row. Excel export consumes this directly."""
        async with self._sf() as session:
            stmt = self._apply_filters(select(TransactionRow), filters).order_by(TransactionRow.created_at.desc())
            result = await session.execute(stmt)
            for row in result.scalars():
                yield _to_domain(row, self._provider)
