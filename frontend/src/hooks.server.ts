import type { Handle, HandleFetch } from '@sveltejs/kit';
import { BACKEND_BASE } from '$lib/server/env';

/**
 * Forward the inbound session cookie to backend fetches.
 *
 * SvelteKit's `event.fetch` by default forwards cookies for same-origin
 * URLs. The backend lives on a different host (BACKEND_BASE), so we'd lose
 * the `caas_session` cookie otherwise. Re-attach it here so server-side
 * load functions stay authenticated.
 */
export const handleFetch: HandleFetch = async ({ request, fetch, event }) => {
  if (request.url.startsWith(BACKEND_BASE)) {
    const cookie = event.request.headers.get('cookie');
    if (cookie) {
      request.headers.set('cookie', cookie);
    }
  }
  return fetch(request);
};

export const handle: Handle = async ({ event, resolve }) => {
  return resolve(event);
};
