"""
RBAC dependency factory used by every protected route.

Typical usage::

    @router.delete(
        "/admin/users/{user_id}",
        dependencies=[Depends(require_permission(Permission.DELETE_USER))],
    )
    async def delete_user(...): ...

The factory returns a FastAPI dependency that:

1. Resolves the principal via :func:`require_admin` (cookie session or
   HTTP Basic for super-admin).
2. Checks the principal's role carries the requested permission.
3. Raises 403 if not, otherwise returns the principal — the route can
   take it as a parameter if it wants to know who's calling.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status

from src.domain import Permission, Role, role_has_permission


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    username: str
    role: Role

    def can(self, perm: Permission) -> bool:
        return role_has_permission(self.role, perm)


def require_permission(perm: Permission):
    # Local import to avoid circular dep with auth.py (which uses
    # AuthenticatedUser from this module).
    from src.infrastructure.http.auth import require_admin

    def dep(user: AuthenticatedUser = Depends(require_admin)) -> AuthenticatedUser:
        if not user.can(perm):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"missing permission: {perm.value}",
            )
        return user

    return dep
