import { redirect } from '@sveltejs/kit';
import { ApiError, auth, currentUserFrom } from '$lib/api/client';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ fetch }) => {
  try {
    const me = await auth.me(fetch);
    return { user: currentUserFrom(me) };
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) {
      throw redirect(302, '/auth/login');
    }
    throw e;
  }
};
