import { redirect, type Actions } from '@sveltejs/kit';
import { auth } from '$lib/api/client';
import { SESSION_COOKIE } from '$lib/server/session';

export const actions: Actions = {
  default: async ({ fetch, cookies }) => {
    try {
      await auth.logout(fetch);
    } catch {
      // ignore — we clear the cookie locally regardless
    }
    cookies.delete(SESSION_COOKIE, { path: '/' });
    throw redirect(303, '/auth/login');
  }
};

export const load = () => {
  // Direct GET → not useful, send the visitor to login.
  throw redirect(303, '/auth/login');
};
