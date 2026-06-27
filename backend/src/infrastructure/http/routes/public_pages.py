"""
Public route for builder-published pages.

Unauthenticated and uncached for now. Returns 404 in two cases that the
caller cannot distinguish:

- unknown slug,
- existing slug but the page is DRAFT.

This is intentional: an unauthenticated visitor must not be able to
probe for in-progress draft URLs.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.application.use_cases import GetPublishedPageBySlug, PageNotFound
from src.domain import Page
from src.infrastructure.http.deps import get_published_page_by_slug_use_case

router = APIRouter(prefix="/pages", tags=["public"])


class BlockPublic(BaseModel):
    id: str
    type: str
    props: dict[str, Any]


class PublicPageResponse(BaseModel):
    slug: str
    title: str
    blocks: list[BlockPublic]
    published_at: str | None


def _to_response(p: Page) -> PublicPageResponse:
    return PublicPageResponse(
        slug=p.slug,
        title=p.title,
        blocks=[BlockPublic(id=b.id, type=b.type, props=b.props) for b in p.blocks],
        published_at=p.published_at.isoformat() if p.published_at else None,
    )


@router.get("/{slug}", response_model=PublicPageResponse)
async def get_public_page(
    slug: str,
    use_case: GetPublishedPageBySlug = Depends(get_published_page_by_slug_use_case),
) -> PublicPageResponse:
    try:
        page = await use_case.execute(slug)
    except PageNotFound:
        raise HTTPException(status_code=404, detail="page not found") from None
    return _to_response(page)
