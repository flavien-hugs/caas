"""
Operator user CRUD.

Thin use cases over :class:`UserRepositoryPort`. They handle:

- the username-uniqueness invariant (returns a domain exception, the HTTP
  layer translates to 409);
- the existence check (404);
- immutable transitions on :class:`User` for partial updates.

The super-admin is **not** managed here — it lives in env, not in the
``users`` table, so these use cases never see it.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.application.ports import UserRepositoryPort
from src.domain import Role, User


class UserNotFound(Exception):
    pass


class UsernameAlreadyTaken(Exception):
    pass


class CannotAssignSuperAdmin(Exception):
    """Raised when create/update tries to set role=SUPER_ADMIN. SA is env-only."""


@dataclass(frozen=True, slots=True)
class CreateUserInput:
    username: str
    password: str
    role: Role


class CreateUser:
    def __init__(self, users: UserRepositoryPort) -> None:
        self._users = users

    async def execute(self, cmd: CreateUserInput) -> User:
        if cmd.role is Role.SUPER_ADMIN:
            raise CannotAssignSuperAdmin
        if await self._users.get_by_username(cmd.username):
            raise UsernameAlreadyTaken(cmd.username)
        user = User.new(username=cmd.username, password=cmd.password, role=cmd.role)
        await self._users.add(user)
        return user


@dataclass(frozen=True, slots=True)
class UpdateUserInput:
    user_id: str
    username: str | None = None
    password: str | None = None
    role: Role | None = None


class UpdateUser:
    def __init__(self, users: UserRepositoryPort) -> None:
        self._users = users

    async def execute(self, cmd: UpdateUserInput) -> User:
        current = await self._users.get(cmd.user_id)
        if current is None:
            raise UserNotFound(cmd.user_id)

        if cmd.role is Role.SUPER_ADMIN:
            raise CannotAssignSuperAdmin

        updated = current
        if cmd.username is not None and cmd.username != current.username:
            clash = await self._users.get_by_username(cmd.username)
            if clash is not None and clash.id != cmd.user_id:
                raise UsernameAlreadyTaken(cmd.username)
            updated = updated.with_username(cmd.username)
        if cmd.password is not None:
            updated = updated.with_password(cmd.password)
        if cmd.role is not None and cmd.role is not current.role:
            updated = updated.with_role(cmd.role)

        await self._users.save(updated)
        return updated


class DeleteUser:
    def __init__(self, users: UserRepositoryPort) -> None:
        self._users = users

    async def execute(self, user_id: str) -> None:
        deleted = await self._users.delete(user_id)
        if not deleted:
            raise UserNotFound(user_id)


class ListUsers:
    def __init__(self, users: UserRepositoryPort) -> None:
        self._users = users

    async def execute(self) -> list[User]:
        return await self._users.list_all()


class GetUser:
    def __init__(self, users: UserRepositoryPort) -> None:
        self._users = users

    async def execute(self, user_id: str) -> User:
        user = await self._users.get(user_id)
        if user is None:
            raise UserNotFound(user_id)
        return user
