import { error } from '@sveltejs/kit';
import { ApiError, dashboard } from '$lib/api/client';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    const stats = await dashboard.stats(fetch);
    return { stats };
  } catch (e) {
    if (e instanceof ApiError && e.status === 403) {
      // User is logged in but lacks READ_STATS — render a stub view
      // instead of a hard error so the sidebar still works.
      return { stats: null, forbidden: true };
    }
    throw error(500, 'Impossible de charger les statistiques.');
  }
};
