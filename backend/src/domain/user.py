"""
Operator user — admin DB row.

Note on the super-admin: the env-keyed credentials
(:py:attr:`Settings.ADMIN_USERNAME` / :py:attr:`Settings.ADMIN_PASSWORD`)
never produce a ``User`` instance. They authenticate directly in
:py:mod:`infrastructure.http.credentials` and carry the ``SUPER_ADMIN``
role at the principal level. Consequence: the super-admin is *structurally*
absent from the users table and from every CRUD response.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime

from .password import hash_password
from .role import Role


@dataclass(frozen=True, slots=True)
class User:
    id: str
    username: str
    password_hash: str
    role: Role
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def new(cls, *, username: str, password: str, role: Role) -> "User":
        if role is Role.SUPER_ADMIN:
            # SUPER_ADMIN is structurally env-only — refusing it here prevents
            # accidental escalation through the CRUD endpoints.
            raise ValueError("cannot create a SUPER_ADMIN user in the DB")
        return cls(
            id=str(uuid.uuid4()),
            username=username.strip(),
            password_hash=hash_password(password),
            role=role,
        )

    def with_password(self, plain: str) -> "User":
        return replace(self, password_hash=hash_password(plain), updated_at=datetime.utcnow())

    def with_username(self, username: str) -> "User":
        return replace(self, username=username.strip(), updated_at=datetime.utcnow())

    def with_role(self, role: Role) -> "User":
        if role is Role.SUPER_ADMIN:
            raise ValueError("cannot promote a DB user to SUPER_ADMIN")
        return replace(self, role=role, updated_at=datetime.utcnow())
