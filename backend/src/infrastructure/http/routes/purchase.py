"""
Routes for the purchase initiation flow.

This module is a thin controller: it translates HTTP DTOs to the use case
input, runs the use case, and translates back. No business logic here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.application.use_cases import (
    InitiatePurchase,
    InitiatePurchaseInput,
    LookupPurchase,
    ProviderInitiationFailed,
    UnknownProduct,
)
from src.domain import Customer
from src.infrastructure.config.settings import settings
from src.infrastructure.http.deps import initiate_purchase_use_case, lookup_purchase_use_case
from src.infrastructure.http.limiter import limiter
from src.infrastructure.http.schemas import (
    PurchaseLookupResponse,
    PurchaseRequest,
    PurchaseResponse,
)

router = APIRouter(tags=["purchase"])

# Empty PURCHASES_RATE_LIMIT (env-config) disables the decorator entirely —
# useful for load tests and for smoke-running the API behind an external
# rate limiter (Cloudflare, nginx) that owns the policy.
_PURCHASE_RATE = settings.PURCHASES_RATE_LIMIT


@router.post(
    "/purchases",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
)
@(limiter.limit(_PURCHASE_RATE) if _PURCHASE_RATE else (lambda f: f))
async def create_purchase(
    request: Request,
    body: PurchaseRequest,
    use_case: InitiatePurchase = Depends(initiate_purchase_use_case),
) -> PurchaseResponse:
    customer = Customer(
        email=str(body.email),
        name=f"{body.name} {body.surname}".strip(),
        phone=body.phone,
        country=body.country,
        city=body.city,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        latitude=body.latitude,
        longitude=body.longitude,
    )
    cmd = InitiatePurchaseInput(
        book_id=body.book_id,
        customer=customer,
        client_amount=body.client_amount,
        offer=body.offer,
        situation=body.situation,
    )

    try:
        result = await use_case.execute(cmd)
    except UnknownProduct as exc:
        raise HTTPException(status_code=404, detail=f"unknown book_id: {exc}") from exc
    except ProviderInitiationFailed as exc:
        raise HTTPException(status_code=502, detail=f"provider initiation failed: {exc}") from exc

    return PurchaseResponse(
        purchase_id=result.purchase_id,
        payment_url=result.payment_url,
        amount=result.server_amount.amount,
        currency=result.server_amount.currency.value,
    )


@router.get("/purchases/{purchase_id}", response_model=PurchaseLookupResponse)
async def get_purchase(
    purchase_id: str,
    use_case: LookupPurchase = Depends(lookup_purchase_use_case),
) -> PurchaseLookupResponse:
    purchase = await use_case.execute(purchase_id)
    if purchase is None:
        raise HTTPException(status_code=404, detail="purchase not found")
    return PurchaseLookupResponse(
        id=purchase.id,
        book_id=purchase.book_id,
        status=purchase.status.value,
        amount=purchase.amount.amount,
        currency=purchase.amount.currency.value,
    )
