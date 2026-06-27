import { fail, redirect, type Actions } from '@sveltejs/kit';
import { ApiError, users, type ApiRole } from '$lib/api/client';

const ROLES: ApiRole[] = ['admin', 'operator', 'reader'];

export const actions: Actions = {
  default: async ({ request, fetch }) => {
    const data = await request.formData();
    const username = String(data.get('username') ?? '').trim();
    const password = String(data.get('password') ?? '');
    const role = String(data.get('role') ?? '') as ApiRole;

    if (!username || !password || !role) {
      return fail(400, { username, role, error: 'Tous les champs sont requis.' });
    }
    if (!ROLES.includes(role)) {
      return fail(400, { username, role, error: 'Rôle invalide.' });
    }
    if (password.length < 8) {
      return fail(400, { username, role, error: 'Mot de passe : 8 caractères minimum.' });
    }
    if (username.length < 3) {
      return fail(400, { username, role, error: 'Nom d’utilisateur : 3 caractères minimum.' });
    }

    let created;
    try {
      created = await users.create(fetch, { username, password, role });
    } catch (e) {
      if (e instanceof ApiError) {
        return fail(e.status, {
          username,
          role,
          error:
            e.status === 409
              ? 'Ce nom d’utilisateur est déjà pris.'
              : e.status === 400
                ? 'Données invalides (le rôle super_admin est interdit).'
                : e.message
        });
      }
      throw e;
    }

    throw redirect(303, `/admin/users/${created.id}`);
  }
};
