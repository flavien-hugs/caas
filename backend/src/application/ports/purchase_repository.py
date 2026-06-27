from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import AsyncIterator, Protocol

from src.domain import Purchase


@dataclass(frozen=True, slots=True)
class TransactionStats:
    total_revenue: float
    successful_sales: int
    pending_transactions: int
    failed_transactions: int
    total_transactions: int


@dataclass(frozen=True, slots=True)
class RevenuePoint:
    day: date
    revenue: float


@dataclass(frozen=True, slots=True)
class PaginatedPurchases:
    items: list[Purchase]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        if self.size <= 0:
            return 0
        return max(1, (self.total + self.size - 1) // self.size)


class PurchaseRepositoryPort(Protocol):
    async def add(self, purchase: Purchase) -> None: ...

    async def get(self, purchase_id: str) -> Purchase | None: ...

    async def get_by_provider_tx_id(self, provider_tx_id: str) -> Purchase | None: ...

    async def save(self, purchase: Purchase) -> None:
        """
        Persist an updated aggregate. Implementations decide their own
        consistency strategy (insert-or-update, optimistic locking, …).
        """
        ...

    async def list_pending(self, book_ids: list[str] | None = None) -> list[Purchase]:
        """
        Used by the reconciliation job (ex-``synchronise.py``).
        """
        ...

    # --- Dashboard read-model --------------------------------------------

    async def list_paginated(self, filters, page: int, size: int) -> PaginatedPurchases:
        """Paginated transaction list for the admin dashboard."""
        ...

    async def compute_stats(self, filters) -> TransactionStats:
        """Aggregate counts + total SUCCESS revenue under the filter."""
        ...

    async def revenue_last_days(self, filters, days: int) -> list[RevenuePoint]:
        """Daily SUCCESS revenue series, last *days* days."""
        ...

    def iter_for_export(self, filters) -> AsyncIterator[Purchase]:
        """Async-iterate every matching row (no pagination). Used by Excel export."""
        ...
