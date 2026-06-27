import { error, fail, redirect } from '@sveltejs/kit';
import { ApiError, pages } from '$lib/api/client';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    const list = await pages.list(fetch);
    return { pages: list };
  } catch (e) {
    if (e instanceof ApiError && e.status === 403) {
      throw error(403, 'Tu n’as pas la permission de gérer les pages.');
    }
    throw error(500, 'Impossible de charger les pages.');
  }
};

export const actions: Actions = {
  create: async ({ request, fetch }) => {
    const data = await request.formData();
    const slug = String(data.get('slug') ?? '').trim();
    const title = String(data.get('title') ?? '').trim();
    if (!slug || !title) {
      return fail(400, { scope: 'create', slug, title, error: 'Slug et titre requis.' });
    }
    try {
      const created = await pages.create(fetch, { slug, title });
      // Open the freshly created page in the builder.
      throw redirect(303, `/admin/pages/${created.id}`);
    } catch (e) {
      if (e instanceof ApiError) {
        return fail(e.status, {
          scope: 'create',
          slug,
          title,
          error:
            e.status === 409
              ? 'Ce slug est déjà utilisé.'
              : e.status === 422
                ? 'Slug invalide (lettres minuscules, chiffres et tirets uniquement).'
                : e.message
        });
      }
      throw e; // re-throw SvelteKit redirect()
    }
  },

  delete: async ({ request, fetch }) => {
    const data = await request.formData();
    const id = String(data.get('id') ?? '').trim();
    if (!id) return fail(400, { scope: 'delete', error: 'ID manquant.' });
    try {
      await pages.remove(fetch, id);
    } catch (e) {
      if (e instanceof ApiError) {
        return fail(e.status, { scope: 'delete', error: e.message });
      }
      throw e;
    }
    throw redirect(303, '/admin/pages');
  }
};
