"""
Admin authentication dependency.

Resolution order (first match wins):

1. **Cookie session** — set by ``POST /auth/login``. Carries username + role.
2. **HTTP Basic** — fallback for curl, scripts, CI. **Super-admin only**;
   DB operator users must go through the login flow (so their role lookup
   stays where it belongs, in the DB).

Returns an :class:`AuthenticatedUser` principal on success. The principal
is consumed by :func:`require_permission` to enforce RBAC.
"""

from __future__ import annotations

import base64

from fastapi import HTTPException, Request, status
from fastapi.security.utils import get_authorization_scheme_param

from src.domain import Role
from src.infrastructure.http.credentials import check_super_admin_credentials
from src.infrastructure.http.rbac import AuthenticatedUser

_SESSION_USER = "admin_username"
_SESSION_ROLE = "admin_role"


def require_admin(request: Request) -> AuthenticatedUser:
    # 1. Session cookie — username + role baked in at login.
    username = request.session.get(_SESSION_USER)
    role_str = request.session.get(_SESSION_ROLE)
    if username and role_str:
        try:
            return AuthenticatedUser(username=username, role=Role(role_str))
        except ValueError:
            # Stale session pointing at a role that no longer exists. Reject.
            pass

    # 2. HTTP Basic — super-admin only (env-keyed, no DB roundtrip).
    authorization = request.headers.get("Authorization")
    if authorization:
        scheme, param = get_authorization_scheme_param(authorization)
        if scheme.lower() == "basic":
            try:
                decoded = base64.b64decode(param).decode()
                user, _, password = decoded.partition(":")
            except (ValueError, UnicodeDecodeError):
                user, password = "", ""
            if check_super_admin_credentials(user, password):
                return AuthenticatedUser(username=user, role=Role.SUPER_ADMIN)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="admin authentication required",
        headers={"WWW-Authenticate": "Basic"},
    )
