import { error, fail } from '@sveltejs/kit';
import { ApiError, users, type ApiRole } from '$lib/api/client';
import type { Actions, PageServerLoad } from './$types';

const ROLES: ApiRole[] = ['admin', 'operator', 'reader'];

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    const list = await users.list(fetch);
    return { users: list };
  } catch (e) {
    if (e instanceof ApiError && e.status === 403) {
      throw error(403, 'Tu n’as pas la permission de voir les utilisateurs.');
    }
    throw error(500, 'Impossible de charger les utilisateurs.');
  }
};

export const actions: Actions = {
  /**
   * Side-drawer creation: succeeds with ``{ created: true, user }`` so the
   * client can close the panel and reload the list. The dedicated
   * ``/admin/users/new`` route still works for direct URL access.
   */
  create: async ({ request, fetch }) => {
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
    if (username.length < 3) {
      return fail(400, { username, role, error: 'Nom d’utilisateur : 3 caractères minimum.' });
    }
    if (password.length < 8) {
      return fail(400, { username, role, error: 'Mot de passe : 8 caractères minimum.' });
    }

    try {
      const created = await users.create(fetch, { username, password, role });
      return { created: true, user: created };
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
  }
};
