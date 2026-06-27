"""SQL implementation of :class:`PageRepositoryPort`."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain import Block, Page, PageStatus
from src.infrastructure.persistence.models import PageRow


def _to_row(p: Page) -> PageRow:
    return PageRow(
        id=p.id,
        slug=p.slug,
        title=p.title,
        blocks=[{"id": b.id, "type": b.type, "props": b.props} for b in p.blocks],
        status=p.status.value,
        created_at=p.created_at,
        updated_at=p.updated_at,
        published_at=p.published_at,
    )


def _to_domain(row: PageRow) -> Page:
    try:
        status = PageStatus(row.status)
    except ValueError:
        # Unknown status value → treat as DRAFT, safest default.
        status = PageStatus.DRAFT
    raw_blocks = row.blocks or []
    blocks = tuple(
        Block(id=str(b["id"]), type=str(b["type"]), props=dict(b.get("props") or {}))
        for b in raw_blocks
        if isinstance(b, dict) and "id" in b and "type" in b
    )
    return Page(
        id=row.id,
        slug=row.slug,
        title=row.title,
        blocks=blocks,
        status=status,
        created_at=row.created_at,
        updated_at=row.updated_at,
        published_at=row.published_at,
    )


class SqlPageRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def add(self, page: Page) -> None:
        async with self._sf() as session:
            session.add(_to_row(page))
            await session.commit()

    async def get(self, page_id: str) -> Page | None:
        async with self._sf() as session:
            row = await session.get(PageRow, page_id)
            return _to_domain(row) if row else None

    async def get_by_slug(self, slug: str) -> Page | None:
        async with self._sf() as session:
            stmt = select(PageRow).where(PageRow.slug == slug)
            row = (await session.execute(stmt)).scalars().first()
            return _to_domain(row) if row else None

    async def save(self, page: Page) -> None:
        async with self._sf() as session:
            row = await session.get(PageRow, page.id)
            new = _to_row(page)
            if row is None:
                session.add(new)
            else:
                for field, value in new.model_dump(exclude={"id"}).items():
                    setattr(row, field, value)
                session.add(row)
            await session.commit()

    async def delete(self, page_id: str) -> bool:
        async with self._sf() as session:
            row = await session.get(PageRow, page_id)
            if row is None:
                return False
            await session.delete(row)
            await session.commit()
            return True

    async def list_all(self) -> list[Page]:
        async with self._sf() as session:
            stmt = select(PageRow).order_by(PageRow.updated_at.desc())
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(r) for r in rows]
