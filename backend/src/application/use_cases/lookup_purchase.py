"""
Use case: fetch a purchase by id.

Backs ``GET /v2/purchases/{id}`` and the SvelteKit server-side guards on
``/payment/success`` and ``/payment/error`` (they must validate that a
purchase exists in a terminal state before rendering, see the policy
mirrored from :py:mod:`app.routers.payment`).
"""

from __future__ import annotations

from src.application.ports import PurchaseRepositoryPort
from src.domain import Purchase


class LookupPurchase:
    def __init__(self, purchases: PurchaseRepositoryPort) -> None:
        self._purchases = purchases

    async def execute(self, purchase_id: str) -> Purchase | None:
        return await self._purchases.get(purchase_id)
