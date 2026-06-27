import { fail, redirect, type Actions } from '@sveltejs/kit';
import { BACKEND_BASE } from '$lib/server/env';

// Cheap RFC-5322-lite check. The backend re-validates credentials; this
// only stops obviously malformed input from hitting the network.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const actions: Actions = {
  default: async ({ request, fetch, cookies, url }) => {
    const data = await request.formData();
    const email = String(data.get('email') ?? '')
      .trim()
      .toLowerCase();
    const password = String(data.get('password') ?? '');

    if (!email || !password) {
      return fail(400, { email, error: 'Email et mot de passe requis.' });
    }
    if (!EMAIL_RE.test(email)) {
      return fail(400, { email, error: 'Adresse email invalide.' });
    }

    try {
      // Login is server-to-server: we need the raw Response to read the
      // Set-Cookie header (SvelteKit's event.fetch does not surface it via
      // the typed `auth.login` wrapper). Forward the session cookie set by
      // the backend onto the browser response via cookies API.
      //
      // The backend's LoginRequest field is `username` (free-form, max 100);
      // we send the email there since the user-identifier is the email.
      const res = await fetch(`${BACKEND_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ username: email, password })
      });
      if (!res.ok) {
        return fail(401, { email, error: 'Identifiants invalides.' });
      }
      const setCookie = res.headers.get('set-cookie');
      if (setCookie) {
        const match = setCookie.match(/caas_session=([^;]+)/);
        if (match) {
          // SvelteKit URL-encodes cookie values by default, which would
          // mutate the backend's signed value (`=` → `%3D`) and break the
          // signature check on the next request. Pass through verbatim.
          cookies.set('caas_session', match[1], {
            path: '/',
            httpOnly: true,
            sameSite: 'lax',
            secure: url.protocol === 'https:',
            maxAge: 60 * 60 * 24 * 7,
            encode: (v) => v
          });
        }
      }
    } catch {
      return fail(500, { email, error: 'Erreur réseau, réessaye.' });
    }

    throw redirect(303, '/admin');
  }
};
