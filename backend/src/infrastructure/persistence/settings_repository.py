"""SQL implementation of :class:`SettingsRepositoryPort`."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain import ConfigSection
from src.infrastructure.persistence.models import AppSettingRow


class SqlAppSettingsRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get(self, section: ConfigSection) -> dict | None:
        async with self._sf() as session:
            row = await session.get(AppSettingRow, section.value)
            return dict(row.value) if row else None

    async def set(self, section: ConfigSection, values: dict) -> None:
        async with self._sf() as session:
            row = await session.get(AppSettingRow, section.value)
            if row is None:
                session.add(AppSettingRow(key=section.value, value=values, updated_at=datetime.utcnow()))
            else:
                row.value = values
                row.updated_at = datetime.utcnow()
                session.add(row)
            await session.commit()

    async def all(self) -> dict[str, dict]:
        async with self._sf() as session:
            rows = (await session.execute(select(AppSettingRow))).scalars().all()
            return {r.key: dict(r.value) for r in rows}
