/**
 * Mirror of the backend RBAC matrix
 * (`backend/src/domain/role.py`).
 *
 * Kept in sync manually for now — it's a small fixed set and code-defined
 * on both sides. When phase 2 moves the matrix to DB we'll fetch it from
 * the backend instead of duplicating.
 *
 * Important: the UI gating below is **convenience only**. The backend
 * enforces every permission via `require_permission(P)`; this file just
 * keeps users from clicking links they'd hit 403 on.
 */

export const Role = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  OPERATOR: 'operator',
  READER: 'reader'
} as const;

export type Role = (typeof Role)[keyof typeof Role];

export const Permission = {
  READ_TRANSACTIONS: 'read:transactions',
  EXPORT_TRANSACTIONS: 'export:transactions',
  SYNC_PAYMENT: 'sync:payment',
  RESEND_DELIVERY: 'resend:delivery',
  READ_STATS: 'read:stats',
  LIST_USERS: 'list:users',
  READ_USER: 'read:user',
  CREATE_USER: 'create:user',
  UPDATE_USER: 'update:user',
  DELETE_USER: 'delete:user',
  MANAGE_PAGES: 'manage:pages',
  MANAGE_SETTINGS: 'manage:settings'
} as const;

export type Permission = (typeof Permission)[keyof typeof Permission];

const ALL: Permission[] = Object.values(Permission);

export const ROLE_PERMISSIONS: Record<Role, ReadonlySet<Permission>> = {
  [Role.SUPER_ADMIN]: new Set(ALL),
  [Role.ADMIN]: new Set([
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
    Permission.MANAGE_SETTINGS
    // NOT DELETE_USER — super-admin only
  ]),
  [Role.OPERATOR]: new Set([
    Permission.READ_TRANSACTIONS,
    Permission.EXPORT_TRANSACTIONS,
    Permission.RESEND_DELIVERY,
    Permission.READ_STATS
  ]),
  [Role.READER]: new Set([Permission.READ_TRANSACTIONS, Permission.READ_STATS])
};

export function can(role: Role | string | undefined, perm: Permission): boolean {
  if (!role) return false;
  const r = role as Role;
  return ROLE_PERMISSIONS[r]?.has(perm) ?? false;
}
