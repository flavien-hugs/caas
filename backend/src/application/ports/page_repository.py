from __future__ import annotations

from typing import Protocol

from src.domain import Page


class PageRepositoryPort(Protocol):
    async def add(self, page: Page) -> None:
        """Insert a new page. Raises if slug already exists."""
        ...

    async def get(self, page_id: str) -> Page | None: ...

    async def get_by_slug(self, slug: str) -> Page | None: ...

    async def save(self, page: Page) -> None:
        """Insert-or-update by primary key."""
        ...

    async def delete(self, page_id: str) -> bool:
        """Returns True if a row was deleted, False if it didn't exist."""
        ...

    async def list_all(self) -> list[Page]:
        """Admin listing — drafts + published, newest first."""
        ...
