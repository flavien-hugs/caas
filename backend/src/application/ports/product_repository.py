from __future__ import annotations

from typing import Protocol

from src.domain import Product


class ProductRepositoryPort(Protocol):
    async def get(self, book_id: str) -> Product | None: ...
