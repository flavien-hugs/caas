"""
Admin credentials check — two layers.

1. **Super-admin** is env-keyed (``ADMIN_USERNAME`` / ``ADMIN_PASSWORD``)
   and compared with :py:func:`secrets.compare_digest`. Never stored in
   the DB, always carries :py:attr:`Role.SUPER_ADMIN` at the principal level.
2. **Operator users** live in the ``users`` table, password bcrypted, role
   stored on the row.

:func:`check_super_admin_credentials` is sync, env-only — used by the HTTP
Basic fallback in :py:func:`require_admin` (no DB roundtrip).
:func:`authenticate` is async, used by the login flow: tries env first,
then the operator users table. Returns an :class:`AuthenticatedUser`
principal carrying the role, or ``None`` on failure.
"""

from __future__ import annotations

import secrets

from src.application.ports import UserRepositoryPort
from src.domain import Role, verify_password
from src.infrastructure.config.settings import settings
from src.infrastructure.http.rbac import AuthenticatedUser


def check_super_admin_credentials(username: str, password: str) -> bool:
    user_ok = secrets.compare_digest(username.encode(), settings.ADMIN_USERNAME.encode())
    pass_ok = secrets.compare_digest(password.encode(), settings.ADMIN_PASSWORD.encode())
    return user_ok and pass_ok


async def authenticate(username: str, password: str, users: UserRepositoryPort) -> AuthenticatedUser | None:
    """Full login check. Returns the principal on success, ``None`` otherwise."""
    if check_super_admin_credentials(username, password):
        return AuthenticatedUser(username=username, role=Role.SUPER_ADMIN)
    user = await users.get_by_username(username)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return AuthenticatedUser(username=user.username, role=user.role)
