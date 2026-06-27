"""
Admin actions: resend delivery, manual sync (confirm by provider_tx_id),
Excel export.

Routes are mounted under ``/admin`` with the basic-auth dependency applied
once at the router level.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.application.dashboard_filters import TransactionFilters
from src.application.use_cases import (
    AdminConfirmPayment,
    AdminConfirmPaymentInput,
    ExportTransactions,
    ProviderTxIdAlreadyLinked,
    PurchaseNotEligibleForResend,
    PurchaseNotFound,
    ResendDelivery,
    ResendDeliveryInput,
)
from src.domain import Permission
from src.infrastructure.http.deps import (
    admin_confirm_payment_use_case,
    export_transactions_use_case,
    resend_delivery_use_case,
)
from src.infrastructure.http.rbac import require_permission
from src.infrastructure.http.schemas import CallbackResponse

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminSyncRequest(BaseModel):
    provider_tx_id: str = Field(min_length=1, max_length=128)


class ResendResponse(BaseModel):
    purchase_id: str
    delivered: bool


@router.post(
    "/transactions/{purchase_id}/resend",
    response_model=ResendResponse,
    dependencies=[Depends(require_permission(Permission.RESEND_DELIVERY))],
)
async def resend(
    purchase_id: str,
    use_case: ResendDelivery = Depends(resend_delivery_use_case),
) -> ResendResponse:
    try:
        purchase = await use_case.execute(ResendDeliveryInput(purchase_id=purchase_id))
    except PurchaseNotFound:
        raise HTTPException(status_code=404, detail="purchase not found") from None
    except PurchaseNotEligibleForResend as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ResendResponse(purchase_id=purchase.id, delivered=True)


@router.post(
    "/transactions/{purchase_id}/sync",
    response_model=CallbackResponse,
    dependencies=[Depends(require_permission(Permission.SYNC_PAYMENT))],
)
async def admin_sync(
    purchase_id: str,
    body: AdminSyncRequest,
    use_case: AdminConfirmPayment = Depends(admin_confirm_payment_use_case),
) -> CallbackResponse:
    try:
        result = await use_case.execute(AdminConfirmPaymentInput(purchase_id=purchase_id, provider_tx_id=body.provider_tx_id))
    except PurchaseNotFound:
        raise HTTPException(status_code=404, detail="purchase not found") from None
    except ProviderTxIdAlreadyLinked as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CallbackResponse(
        purchase_id=result.purchase.id,
        status=result.purchase.status.value,
        confirmed=result.confirmed,
        delivered=result.delivered,
    )


@router.get(
    "/transactions/export.xlsx",
    dependencies=[Depends(require_permission(Permission.EXPORT_TRANSACTIONS))],
)
async def export_xlsx(
    q: str | None = Query(None, alias="search"),
    status_: Annotated[str | None, Query(alias="status")] = None,
    book_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    include_low_amount: bool = False,
    use_case: ExportTransactions = Depends(export_transactions_use_case),
) -> StreamingResponse:
    filters = TransactionFilters(
        q=q,
        status=status_,
        book_id=book_id,
        start_date=start_date,
        end_date=end_date,
        include_low_amount=include_low_amount,
        min_amount=0,  # phase 1: no min_price catalog; mirror dashboard behaviour later
    )
    payload = await use_case.execute(filters)
    return StreamingResponse(
        BytesIO(payload),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="transactions.xlsx"'},
    )
