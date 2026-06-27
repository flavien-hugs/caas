from __future__ import annotations

from typing import Protocol

from src.domain import User


class UserRepositoryPort(Protocol):
    async def add(self, user: User) -> None: ...

    async def get(self, user_id: str) -> User | None: ...

    async def get_by_username(self, username: str) -> User | None: ...

    async def save(self, user: User) -> None:
        """Insert-or-update by primary key."""
        ...

    async def delete(self, user_id: str) -> bool:
        """Returns True if a row was deleted, False if it didn't exist."""
        ...

    async def list_all(self) -> list[User]: ...
