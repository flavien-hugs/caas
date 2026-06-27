import type { Role } from '$lib/permissions';

export interface CurrentUser {
  username: string;
  role: Role | string;
}

/** Cookie name used by backend SessionMiddleware (`SESSION_COOKIE_NAME`). */
export const SESSION_COOKIE = 'caas_session';
