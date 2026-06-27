"""
Admin Page CRUD routes — all guarded by ``MANAGE_PAGES``.

Block payload structure (``{id, type, props}``) is preserved verbatim
through the API; the backend does no per-type schema validation. Block
schemas live in the SvelteKit frontend (Zod), keeping the per-type
contract in a single place so adding a new block doesn't require a
backend deploy.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.application.use_cases import (
    CreatePage,
    CreatePageInput,
    DeletePage,
    GetPage,
    ListPages,
    PageNotFound,
    PublishPage,
    SlugAlreadyTaken,
    UnpublishPage,
    UpdatePage,
    UpdatePageInput,
)
from src.domain import Page, Permission
from src.infrastructure.http.deps import (
    create_page_use_case,
    delete_page_use_case,
    get_page_use_case,
    list_pages_use_case,
    publish_page_use_case,
    unpublish_page_use_case,
    update_page_use_case,
)
from src.infrastructure.http.rbac import require_permission

router = APIRouter(prefix="/admin/pages", tags=["admin"])


class BlockBody(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)
    props: dict[str, Any] = Field(default_factory=dict)


class CreatePageBody(BaseModel):
    slug: str = Field(min_length=2, max_length=100)
    title: str = Field(min_length=1, max_length=200)


class UpdatePageBody(BaseModel):
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    blocks: list[BlockBody] | None = None


class PageResponse(BaseModel):
    id: str
    slug: str
    title: str
    blocks: list[BlockBody]
    status: str
    created_at: str
    updated_at: str
    published_at: str | None


def _to_response(p: Page) -> PageResponse:
    return PageResponse(
        id=p.id,
        slug=p.slug,
        title=p.title,
        blocks=[BlockBody(id=b.id, type=b.type, props=b.props) for b in p.blocks],
        status=p.status.value,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
        published_at=p.published_at.isoformat() if p.published_at else None,
    )


@router.get(
    "",
    response_model=list[PageResponse],
    dependencies=[Depends(require_permission(Permission.MANAGE_PAGES))],
)
async def list_pages(use_case: ListPages = Depends(list_pages_use_case)) -> list[PageResponse]:
    return [_to_response(p) for p in await use_case.execute()]


@router.post(
    "",
    response_model=PageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MANAGE_PAGES))],
)
async def create_page(
    body: CreatePageBody,
    use_case: CreatePage = Depends(create_page_use_case),
) -> PageResponse:
    try:
        page = await use_case.execute(CreatePageInput(slug=body.slug, title=body.title))
    except SlugAlreadyTaken:
        raise HTTPException(status_code=409, detail=f"slug already taken: {body.slug!r}") from None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return _to_response(page)


@router.get(
    "/{page_id}",
    response_model=PageResponse,
    dependencies=[Depends(require_permission(Permission.MANAGE_PAGES))],
)
async def get_page(page_id: str, use_case: GetPage = Depends(get_page_use_case)) -> PageResponse:
    try:
        page = await use_case.execute(page_id)
    except PageNotFound:
        raise HTTPException(status_code=404, detail="page not found") from None
    return _to_response(page)


@router.patch(
    "/{page_id}",
    response_model=PageResponse,
    dependencies=[Depends(require_permission(Permission.MANAGE_PAGES))],
)
async def update_page(
    page_id: str,
    body: UpdatePageBody,
    use_case: UpdatePage = Depends(update_page_use_case),
) -> PageResponse:
    try:
        page = await use_case.execute(
            UpdatePageInput(
                page_id=page_id,
                slug=body.slug,
                title=body.title,
                blocks=[b.model_dump() for b in body.blocks] if body.blocks is not None else None,
            )
        )
    except PageNotFound:
        raise HTTPException(status_code=404, detail="page not found") from None
    except SlugAlreadyTaken:
        raise HTTPException(status_code=409, detail=f"slug already taken: {body.slug!r}") from None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return _to_response(page)


@router.post(
    "/{page_id}/publish",
    response_model=PageResponse,
    dependencies=[Depends(require_permission(Permission.MANAGE_PAGES))],
)
async def publish_page(
    page_id: str,
    use_case: PublishPage = Depends(publish_page_use_case),
) -> PageResponse:
    try:
        page = await use_case.execute(page_id)
    except PageNotFound:
        raise HTTPException(status_code=404, detail="page not found") from None
    return _to_response(page)


@router.post(
    "/{page_id}/unpublish",
    response_model=PageResponse,
    dependencies=[Depends(require_permission(Permission.MANAGE_PAGES))],
)
async def unpublish_page(
    page_id: str,
    use_case: UnpublishPage = Depends(unpublish_page_use_case),
) -> PageResponse:
    try:
        page = await use_case.execute(page_id)
    except PageNotFound:
        raise HTTPException(status_code=404, detail="page not found") from None
    return _to_response(page)


@router.delete(
    "/{page_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.MANAGE_PAGES))],
)
async def delete_page(page_id: str, use_case: DeletePage = Depends(delete_page_use_case)) -> None:
    try:
        await use_case.execute(page_id)
    except PageNotFound:
        raise HTTPException(status_code=404, detail="page not found") from None
