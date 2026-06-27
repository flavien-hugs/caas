"""
POST /v2/payment/beacon — durably link the Kkiapay transactionId to the
internal purchase, called from the SvelteKit widget via
``navigator.sendBeacon`` right before the success/failure redirect.

Returns 204 in every case (the browser may be unloading and a real status
code would be wasted bytes). The use case decides idempotently whether to
write or skip.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from src.application.use_cases import RecordBeacon, RecordBeaconInput
from src.infrastructure.http.deps import record_beacon_use_case
from src.infrastructure.http.schemas import BeaconRequest

router = APIRouter(tags=["payment"])


@router.post("/payment/beacon", status_code=204)
async def beacon(
    body: BeaconRequest,
    use_case: RecordBeacon = Depends(record_beacon_use_case),
) -> Response:
    await use_case.execute(RecordBeaconInput(purchase_id=body.internal_tx_id, provider_tx_id=body.transaction_id))
    return Response(status_code=204)
