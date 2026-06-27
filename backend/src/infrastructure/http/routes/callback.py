"""
GET /v2/payment/callback — invoked by the Kkiapay widget redirect after the
user finishes (or cancels) the payment. Confirms the payment server-side
(authoritative ``verify_payment`` call) and dispatches delivery when needed.

Note: phase 1 is API-only — the front does the post-callback redirect to
``/payment/success`` or ``/payment/error``. This endpoint just returns JSON
describing the outcome so SvelteKit can decide where to send the user.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.use_cases import (
    ConfirmPayment,
    ConfirmPaymentInput,
    PurchaseNotFound,
)
from src.infrastructure.http.deps import confirm_payment_use_case
from src.infrastructure.http.schemas import CallbackResponse

router = APIRouter(tags=["payment"])


@router.get("/payment/callback", response_model=CallbackResponse)
async def callback(
    internal_tx_id: str = Query(..., min_length=1),
    transaction_id: str = Query(..., min_length=1),
    use_case: ConfirmPayment = Depends(confirm_payment_use_case),
) -> CallbackResponse:
    try:
        result = await use_case.execute(ConfirmPaymentInput(purchase_id=internal_tx_id, provider_tx_id=transaction_id))
    except PurchaseNotFound as exc:
        raise HTTPException(status_code=404, detail="purchase not found") from exc

    return CallbackResponse(
        purchase_id=result.purchase.id,
        status=result.purchase.status.value,
        confirmed=result.confirmed,
        delivered=result.delivered,
    )
