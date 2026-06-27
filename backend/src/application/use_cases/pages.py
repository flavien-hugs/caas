"""
Page CRUD + publish/unpublish use cases.

These are thin wrappers over :class:`PageRepositoryPort` that enforce:

- slug uniqueness on create and rename (returns a domain exception, the
  HTTP layer translates to 409);
- existence checks (404);
- the draft-vs-published distinction for the public ``GET /pages/{slug}``
  route (``PageNotPublished`` → 404, never leaks the page's existence).

Block-list validation lives client-side (Zod). The backend stores
``Block.props`` opaquely; adding a new block type doesn't require a
backend release.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.application.ports import PageRepositoryPort
from src.domain import Block, Page, normalize_slug


class PageNotFound(Exception):
    pass


class SlugAlreadyTaken(Exception):
    pass


class PageNotPublished(Exception):
    """Raised when the public route requests a slug that exists only as DRAFT."""


@dataclass(frozen=True, slots=True)
class CreatePageInput:
    slug: str
    title: str


class CreatePage:
    def __init__(self, pages: PageRepositoryPort) -> None:
        self._pages = pages

    async def execute(self, cmd: CreatePageInput) -> Page:
        slug = normalize_slug(cmd.slug)
        if await self._pages.get_by_slug(slug):
            raise SlugAlreadyTaken(slug)
        page = Page.new(slug=slug, title=cmd.title)
        await self._pages.add(page)
        return page


@dataclass(frozen=True, slots=True)
class UpdatePageInput:
    page_id: str
    title: str | None = None
    slug: str | None = None
    blocks: list[dict[str, Any]] | None = None


class UpdatePage:
    """Partial update: title, slug, and/or block list.

    Status is never modified here — Publish/Unpublish own that transition.
    Block payloads come in as raw dicts ``{id, type, props}``; we convert
    to :class:`Block` records, keeping ids as-supplied (so the client can
    drive id allocation for fresh blocks via uuid).
    """

    def __init__(self, pages: PageRepositoryPort) -> None:
        self._pages = pages

    async def execute(self, cmd: UpdatePageInput) -> Page:
        current = await self._pages.get(cmd.page_id)
        if current is None:
            raise PageNotFound(cmd.page_id)

        updated = current
        if cmd.title is not None and cmd.title.strip() != current.title:
            updated = updated.with_title(cmd.title)
        if cmd.slug is not None:
            new_slug = normalize_slug(cmd.slug)
            if new_slug != current.slug:
                clash = await self._pages.get_by_slug(new_slug)
                if clash is not None and clash.id != cmd.page_id:
                    raise SlugAlreadyTaken(new_slug)
                # No setter on Page for slug — use replace via with_blocks/with_title
                # is too narrow. Reach for dataclass.replace directly.
                from dataclasses import replace
                from datetime import datetime, timezone

                updated = replace(updated, slug=new_slug, updated_at=datetime.now(timezone.utc))
        if cmd.blocks is not None:
            blocks = tuple(Block(id=str(b["id"]), type=str(b["type"]), props=dict(b.get("props") or {})) for b in cmd.blocks)
            updated = updated.with_blocks(blocks)

        await self._pages.save(updated)
        return updated


class PublishPage:
    def __init__(self, pages: PageRepositoryPort) -> None:
        self._pages = pages

    async def execute(self, page_id: str) -> Page:
        current = await self._pages.get(page_id)
        if current is None:
            raise PageNotFound(page_id)
        published = current.publish()
        await self._pages.save(published)
        return published


class UnpublishPage:
    def __init__(self, pages: PageRepositoryPort) -> None:
        self._pages = pages

    async def execute(self, page_id: str) -> Page:
        current = await self._pages.get(page_id)
        if current is None:
            raise PageNotFound(page_id)
        unpublished = current.unpublish()
        await self._pages.save(unpublished)
        return unpublished


class DeletePage:
    def __init__(self, pages: PageRepositoryPort) -> None:
        self._pages = pages

    async def execute(self, page_id: str) -> None:
        deleted = await self._pages.delete(page_id)
        if not deleted:
            raise PageNotFound(page_id)


class ListPages:
    def __init__(self, pages: PageRepositoryPort) -> None:
        self._pages = pages

    async def execute(self) -> list[Page]:
        return await self._pages.list_all()


class GetPage:
    def __init__(self, pages: PageRepositoryPort) -> None:
        self._pages = pages

    async def execute(self, page_id: str) -> Page:
        page = await self._pages.get(page_id)
        if page is None:
            raise PageNotFound(page_id)
        return page


class GetPublishedPageBySlug:
    """Public lookup: only returns the page if it is PUBLISHED.

    Raises :class:`PageNotFound` whether the slug is unknown OR the page is
    a DRAFT. We don't surface DRAFT-ness publicly — the route returns 404
    in both cases, so an unauthenticated visitor can't probe for draft URLs.
    """

    def __init__(self, pages: PageRepositoryPort) -> None:
        self._pages = pages

    async def execute(self, slug: str) -> Page:
        page = await self._pages.get_by_slug(slug)
        if page is None or not page.is_published:
            raise PageNotFound(slug)
        return page
