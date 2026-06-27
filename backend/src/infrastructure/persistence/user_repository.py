"""SQL implementation of :class:`UserRepositoryPort`."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain import Role, User
from src.infrastructure.persistence.models import UserRow


def _to_row(u: User) -> UserRow:
    return UserRow(
        id=u.id,
        username=u.username,
        password_hash=u.password_hash,
        role=u.role.value,
        created_at=u.created_at,
        updated_at=u.updated_at,
    )


def _to_domain(row: UserRow) -> User:
    try:
        role = Role(row.role)
    except ValueError:
        # Unknown role value (corrupt or future-rolled-back) → degrade to
        # READER, the least-privileged role.
        role = Role.READER
    return User(
        id=row.id,
        username=row.username,
        password_hash=row.password_hash,
        role=role,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlUserRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def add(self, user: User) -> None:
        async with self._sf() as session:
            session.add(_to_row(user))
            await session.commit()

    async def get(self, user_id: str) -> User | None:
        async with self._sf() as session:
            row = await session.get(UserRow, user_id)
            return _to_domain(row) if row else None

    async def get_by_username(self, username: str) -> User | None:
        async with self._sf() as session:
            stmt = select(UserRow).where(UserRow.username == username)
            row = (await session.execute(stmt)).scalars().first()
            return _to_domain(row) if row else None

    async def save(self, user: User) -> None:
        async with self._sf() as session:
            row = await session.get(UserRow, user.id)
            new = _to_row(user)
            if row is None:
                session.add(new)
            else:
                for field, value in new.model_dump(exclude={"id"}).items():
                    setattr(row, field, value)
                session.add(row)
            await session.commit()

    async def delete(self, user_id: str) -> bool:
        async with self._sf() as session:
            row = await session.get(UserRow, user_id)
            if row is None:
                return False
            await session.delete(row)
            await session.commit()
            return True

    async def list_all(self) -> list[User]:
        async with self._sf() as session:
            stmt = select(UserRow).order_by(UserRow.created_at.desc())
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(r) for r in rows]
