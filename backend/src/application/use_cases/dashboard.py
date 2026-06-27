"""Dashboard read-side use cases.

All three are thin orchestrators over the repository's read-model methods.
They exist mostly to keep the HTTP layer ignorant of SQL aggregation and to
give us a place to add caching later (the CachePort wiring already exists).
"""

from __future__ import annotations

from src.application.dashboard_filters import TransactionFilters
from src.application.ports import PurchaseRepositoryPort
from src.application.ports.purchase_repository import (
    PaginatedPurchases,
    RevenuePoint,
    TransactionStats,
)


class ListTransactions:
    def __init__(self, purchases: PurchaseRepositoryPort) -> None:
        self._purchases = purchases

    async def execute(self, filters: TransactionFilters, page: int, size: int) -> PaginatedPurchases:
        return await self._purchases.list_paginated(filters, page=page, size=size)


class ComputeDashboardStats:
    def __init__(self, purchases: PurchaseRepositoryPort) -> None:
        self._purchases = purchases

    async def execute(self, filters: TransactionFilters) -> TransactionStats:
        return await self._purchases.compute_stats(filters)


class ComputeRevenueChart:
    DEFAULT_DAYS = 30

    def __init__(self, purchases: PurchaseRepositoryPort) -> None:
        self._purchases = purchases

    async def execute(self, filters: TransactionFilters, days: int = DEFAULT_DAYS) -> list[RevenuePoint]:
        return await self._purchases.revenue_last_days(filters, days=days)
