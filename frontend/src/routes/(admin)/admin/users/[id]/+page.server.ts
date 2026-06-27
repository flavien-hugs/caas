import { error, fail, redirect } from '@sveltejs/kit';
import { ApiError, users, type ApiRole, type UpdateUserBody } from '$lib/api/client';
import type { Actions, PageServerLoad } from './$types';

const ROLES: ApiRole[] = ['admin', 'operator', 'reader'];

export const load: PageServerLoad = async ({ params, fetch }) => {
  try {
    const user = await users.get(fetch, params.id);
    return { user };
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      throw error(404, 'Utilisateur introuvable.');
    }
    if (e instanceof ApiError && e.status === 403) {
      throw error(403, 'Tu n’as pas la permission d’accéder à cet utilisateur.');
    }
    throw error(500, 'Impossible de charger l’utilisateur.');
  }
};

export const actions: Actions = {
  update: async ({ params, request, fetch }) => {
    const data = await request.formData();
    const username = String(data.get('username') ?? '').trim();
    const password = String(data.get('password') ?? '');
    const role = String(data.get('role') ?? '') as ApiRole;

    if (!username || !role) {
      return fail(400, { error: 'Nom d’utilisateur et rôle requis.' });
    }
    if (!ROLES.includes(role)) {
      return fail(400, { error: 'Rôle invalide.' });
    }
    if (password && password.length < 8) {
      return fail(400, {
        error: 'Mot de passe : 8 caractères minimum (ou laisse vide pour ne pas changer).'
      });
    }

    const body: UpdateUserBody = { username, role };
    if (password) body.password = password;

    try {
      const updated = await users.update(fetch, params.id, body);
      return { saved: true, user: updated };
    } catch (e) {
      if (e instanceof ApiError) {
        return fail(e.status, {
          error:
            e.status === 409
              ? 'Ce nom d’utilisateur est déjà pris.'
              : e.status === 404
                ? 'Utilisateur introuvable.'
                : e.message
        });
      }
      throw e;
    }
  },

  delete: async ({ params, fetch }) => {
    try {
      await users.remove(fetch, params.id);
    } catch (e) {
      if (e instanceof ApiError) {
        return fail(e.status, {
          error:
            e.status === 403
              ? 'Seul le super-admin peut supprimer un utilisateur.'
              : e.status === 404
                ? 'Utilisateur déjà supprimé.'
                : e.message
        });
      }
      throw e;
    }
    throw redirect(303, '/admin/users');
  }
};
