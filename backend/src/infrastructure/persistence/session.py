"""
Async engine + session factory.

A single engine per process keyed by URL; tests pass an explicit URL pointing
to SQLite in-memory or a temp file.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.config.settings import settings


@lru_cache
def get_engine(url: str | None = None) -> AsyncEngine:
    target = url or settings.DATABASE_URL
    return create_async_engine(target, echo=False, future=True)


@lru_cache
def get_session_factory(url: str | None = None) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(url),
        class_=AsyncSession,
        expire_on_commit=False,
    )


@asynccontextmanager
async def session_scope(url: str | None = None) -> AsyncIterator[AsyncSession]:
    """Convenience context manager for one-off scripts and tests."""
    factory = get_session_factory(url)
    async with factory() as session:
        yield session
