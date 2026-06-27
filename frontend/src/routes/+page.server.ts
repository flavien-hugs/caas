import { redirect } from '@sveltejs/kit';

/** Root: redirect to /admin (which itself redirects to /auth/login if no session). */
export const load = () => {
  throw redirect(302, '/admin');
};
