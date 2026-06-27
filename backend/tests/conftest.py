"""
Shared fixtures.

The ``db_session_factory`` fixture spins up SQLite in-memory, creates the
schema, and registers itself with the composition root so any use case
resolved by the HTTP layer hits the test DB.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.config.settings import settings
from src.infrastructure.http.app import create_app
from src.infrastructure.http.deps import set_session_factory
from src.infrastructure.http.limiter import reset_limiter
from src.infrastructure.persistence import models  # noqa: F401  — register tables on SQLModel.metadata


@pytest.fixture(autouse=True)
def _force_test_admin_credentials():
    """Pin super-admin to ``admin/admin`` for the test run regardless of the
    developer's local ``.env``. Tests hard-code these in ``_basic(...)``; if
    a contributor sets ``ADMIN_USERNAME`` / ``ADMIN_PASSWORD`` to a real
    email + password for local dev, the suite would otherwise blow up with
    cryptic 401s on every admin-protected route."""
    saved_user, saved_pass = settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD
    settings.ADMIN_USERNAME = "admin"
    settings.ADMIN_PASSWORD = "admin"
    yield
    settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD = saved_user, saved_pass


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Each test gets a fresh slowapi storage. The limiter singleton is
    shared across ``create_app()`` calls, so without this fixture the
    integration tests that POST several purchases would bleed quota
    between tests and flake randomly."""
    reset_limiter()
    yield
    reset_limiter()


@pytest.fixture
async def engine() -> AsyncEngine:
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def db_session_factory(engine: AsyncEngine):
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    set_session_factory(factory)
    yield factory
    set_session_factory(None)


@pytest.fixture
async def client(db_session_factory):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
