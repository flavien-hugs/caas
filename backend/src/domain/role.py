"""
Role-based access control primitives.

Phase 1 keeps the matrix small and code-defined: roles and permissions are
StrEnums and the ``Role → frozenset[Permission]`` mapping lives in this
module. The route layer never enumerates permissions itself — it asks
:py:func:`require_permission(P)`, the principal's role drives the check.

Phase 2 moves the mapping to DB (per-tenant role customization). The call
sites stay identical.
"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    SUPER_ADMIN = "super_admin"  # env-keyed, all permissions
    ADMIN = "admin"  # full admin in DB (cannot delete users — SA only)
    OPERATOR = "operator"  # day-to-day ops: read + resend + export
    READER = "reader"  # read-only


class Permission(StrEnum):
    # Transactions
    READ_TRANSACTIONS = "read:transactions"
    EXPORT_TRANSACTIONS = "export:transactions"
    SYNC_PAYMENT = "sync:payment"
    RESEND_DELIVERY = "resend:delivery"
    # Dashboard
    READ_STATS = "read:stats"
    # User management
    LIST_USERS = "list:users"
    READ_USER = "read:user"
    CREATE_USER = "create:user"
    UPDATE_USER = "update:user"
    DELETE_USER = "delete:user"
    # Pages (CMS / page builder)
    MANAGE_PAGES = "manage:pages"
    # Runtime configuration (SMTP, payment aggregators, SMS)
    MANAGE_SETTINGS = "manage:settings"


_ALL: frozenset[Permission] = frozenset(Permission)

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.SUPER_ADMIN: _ALL,
    Role.ADMIN: frozenset(
        {
            Permission.READ_TRANSACTIONS,
            Permission.EXPORT_TRANSACTIONS,
            Permission.SYNC_PAYMENT,
            Permission.RESEND_DELIVERY,
            Permission.READ_STATS,
            Permission.LIST_USERS,
            Permission.READ_USER,
            Permission.CREATE_USER,
            Permission.UPDATE_USER,
            Permission.MANAGE_PAGES,
            Permission.MANAGE_SETTINGS,
            # NOT DELETE_USER — super-admin only
        }
    ),
    Role.OPERATOR: frozenset(
        {
            Permission.READ_TRANSACTIONS,
            Permission.EXPORT_TRANSACTIONS,
            Permission.RESEND_DELIVERY,
            Permission.READ_STATS,
        }
    ),
    Role.READER: frozenset(
        {
            Permission.READ_TRANSACTIONS,
            Permission.READ_STATS,
        }
    ),
}


def role_has_permission(role: Role, perm: Permission) -> bool:
    return perm in ROLE_PERMISSIONS.get(role, frozenset())
