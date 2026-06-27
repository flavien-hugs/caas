"""Admin dashboard read endpoints (transactions list, stats, revenue chart).

All routes here are protected by :func:`require_permission`. Each route
declares its specific permission so the role matrix is enforced uniformly.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.application.dashboard_filters import TransactionFilters
from src.application.use_cases.dashboard import (
    ComputeDashboardStats,
    ComputeRevenueChart,
    ListTransactions,
)
from src.domain import Permission
from src.infrastructure.config.settings import settings
from src.infrastructure.http.deps import (
    compute_dashboard_stats_use_case,
    compute_revenue_chart_use_case,
    list_transactions_use_case,
)
from src.infrastructure.http.rbac import require_permission
from src.infrastructure.http.schemas import (
    DashboardStatsResponse,
    PaginatedTransactions,
    RevenueChartResponse,
    RevenuePointResponse,
    TransactionItem,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _resolved_filters(
    q: str | None,
    status_: str | None,
    book_id: str | None,
    start_date: date | None,
    end_date: date | None,
    include_low_amount: bool,
) -> TransactionFilters:
    # Legacy behaviour: hide transactions below ``min(prices)`` unless the
    # admin explicitly opts in. min_amount is resolved in the HTTP layer so
    # the use case doesn't need to know about settings.
    min_amount = (
        0
        if include_low_amount
        else (
            min(
                settings.DOCUMENT_PDF_PRICE,
                settings.DOCUMENT_FULL_PRICE,
                settings.CERTIF_PRICE,
            )
            if hasattr(settings, "DOCUMENT_PDF_PRICE")
            else 0
        )
    )
    return TransactionFilters(
        q=q,
        status=status_,
        book_id=book_id,
        start_date=start_date,
        end_date=end_date,
        include_low_amount=include_low_amount,
        min_amount=min_amount,
    )


@router.get(
    "/transactions",
    response_model=PaginatedTransactions,
    dependencies=[Depends(require_permission(Permission.READ_TRANSACTIONS))],
)
async def list_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    q: str | None = Query(None, alias="search"),
    status_: Annotated[str | None, Query(alias="status")] = None,
    book_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    include_low_amount: bool = False,
    use_case: ListTransactions = Depends(list_transactions_use_case),
) -> PaginatedTransactions:
    filters = _resolved_filters(q, status_, book_id, start_date, end_date, include_low_amount)
    result = await use_case.execute(filters, page=page, size=size)
    return PaginatedTransactions(
        items=[
            TransactionItem(
                id=p.id,
                book_id=p.book_id,
                user_email=p.customer.email,
                user_name=p.customer.name,
                user_phone=p.customer.phone,
                user_country=p.customer.country,
                user_city=p.customer.city,
                amount=p.amount.amount,
                currency=p.amount.currency.value,
                status=p.status.value,
                transaction_id=p.payment_ref.provider_tx_id,
                created_at=p.created_at.isoformat(),
            )
            for p in result.items
        ],
        total=result.total,
        page=result.page,
        size=result.size,
        pages=result.pages,
    )


@router.get(
    "/dashboard/stats",
    response_model=DashboardStatsResponse,
    dependencies=[Depends(require_permission(Permission.READ_STATS))],
)
async def stats(
    q: str | None = Query(None, alias="search"),
    status_: Annotated[str | None, Query(alias="status")] = None,
    book_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    include_low_amount: bool = False,
    use_case: ComputeDashboardStats = Depends(compute_dashboard_stats_use_case),
) -> DashboardStatsResponse:
    filters = _resolved_filters(q, status_, book_id, start_date, end_date, include_low_amount)
    s = await use_case.execute(filters)
    return DashboardStatsResponse(
        total_revenue=s.total_revenue,
        successful_sales=s.successful_sales,
        pending_transactions=s.pending_transactions,
        failed_transactions=s.failed_transactions,
        total_transactions=s.total_transactions,
    )


@router.get(
    "/dashboard/revenue",
    response_model=RevenueChartResponse,
    dependencies=[Depends(require_permission(Permission.READ_STATS))],
)
async def revenue_chart(
    days: int = Query(30, ge=1, le=365),
    q: str | None = Query(None, alias="search"),
    status_: Annotated[str | None, Query(alias="status")] = None,
    book_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    include_low_amount: bool = False,
    use_case: ComputeRevenueChart = Depends(compute_revenue_chart_use_case),
) -> RevenueChartResponse:
    filters = _resolved_filters(q, status_, book_id, start_date, end_date, include_low_amount)
    series = await use_case.execute(filters, days=days)
    return RevenueChartResponse(
        days=days,
        series=[RevenuePointResponse(day=p.day.isoformat(), revenue=p.revenue) for p in series],
    )
