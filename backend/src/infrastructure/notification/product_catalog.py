"""
In-memory ProductRepository keyed by env-driven settings.

Phase 1: a single product (``lutte-contre-fraude``) — the migration target.
Other products stay served by ``app/`` until they are migrated in their own
strangler step. Phase 2 will replace this with a DB-backed repository scoped
per tenant.
"""

from __future__ import annotations

from src.domain import Currency, DeliveryMethod, Money, Product
from src.infrastructure.config.settings import Settings


class InMemoryProductRepository:
    def __init__(self, settings: Settings) -> None:
        self._catalog: dict[str, Product] = {
            "lutte-contre-fraude": Product(
                book_id="lutte-contre-fraude",
                name="Webinaire — Lutte contre le vol & la fraude",
                price=Money(amount=settings.FRAUDE_WEBINAIRE_PRICE, currency=Currency.XOF),
                delivery_method=DeliveryMethod.WHATSAPP,
                delivery_payload=settings.FRAUDE_WHATSAPP_GROUP_LINK,
            ),
        }

    async def get(self, book_id: str) -> Product | None:
        return self._catalog.get(book_id)
