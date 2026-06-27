import { error, fail, redirect } from '@sveltejs/kit';
import { ApiError, pages, type ApiBlock } from '$lib/api/client';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, fetch }) => {
  try {
    const page = await pages.get(fetch, params.id);
    return { page };
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      throw error(404, 'Page introuvable.');
    }
    if (e instanceof ApiError && e.status === 403) {
      throw error(403, 'Tu n’as pas la permission de gérer les pages.');
    }
    throw error(500, 'Impossible de charger la page.');
  }
};

export const actions: Actions = {
  save: async ({ params, request, fetch }) => {
    const data = await request.formData();
    const title = String(data.get('title') ?? '').trim();
    const slug = String(data.get('slug') ?? '').trim();
    let blocks: ApiBlock[];
    try {
      blocks = JSON.parse(String(data.get('blocks') ?? '[]')) as ApiBlock[];
    } catch {
      return fail(400, { error: 'Payload blocks malformé.' });
    }

    try {
      const updated = await pages.update(fetch, params.id, { title, slug, blocks });
      return { saved: true, page: updated };
    } catch (e) {
      if (e instanceof ApiError) {
        return fail(e.status, {
          error:
            e.status === 409
              ? 'Ce slug est déjà utilisé.'
              : e.status === 422
                ? 'Slug invalide.'
                : e.message
        });
      }
      throw e;
    }
  },

  publish: async ({ params, fetch }) => {
    try {
      const updated = await pages.publish(fetch, params.id);
      return { published: true, page: updated };
    } catch (e) {
      if (e instanceof ApiError) return fail(e.status, { error: e.message });
      throw e;
    }
  },

  unpublish: async ({ params, fetch }) => {
    try {
      const updated = await pages.unpublish(fetch, params.id);
      return { unpublished: true, page: updated };
    } catch (e) {
      if (e instanceof ApiError) return fail(e.status, { error: e.message });
      throw e;
    }
  },

  delete: async ({ params, fetch }) => {
    try {
      await pages.remove(fetch, params.id);
    } catch (e) {
      if (e instanceof ApiError) return fail(e.status, { error: e.message });
      throw e;
    }
    throw redirect(303, '/admin/pages');
  }
};
