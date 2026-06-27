"""SQL implementation of :class:`FeedbackRepositoryPort`."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.feedback import Feedback
from src.infrastructure.persistence.models import FeedbackRow


def _to_row(f: Feedback) -> FeedbackRow:
    return FeedbackRow(
        id=f.id,
        user_name=f.user_name,
        rating=f.rating,
        message=f.message,
        created_at=f.created_at,
    )


def _to_domain(row: FeedbackRow) -> Feedback:
    return Feedback(
        id=row.id,
        user_name=row.user_name,
        rating=row.rating,
        message=row.message,
        created_at=row.created_at,
    )


class SqlFeedbackRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def add(self, feedback: Feedback) -> None:
        async with self._sf() as session:
            session.add(_to_row(feedback))
            await session.commit()

    async def list_recent_high_rated(self, min_rating: int = 4, limit: int = 10) -> list[Feedback]:
        async with self._sf() as session:
            stmt = (
                select(FeedbackRow).where(FeedbackRow.rating >= min_rating).order_by(FeedbackRow.created_at.desc()).limit(limit)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(r) for r in rows]
