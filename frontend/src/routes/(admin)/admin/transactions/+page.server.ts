import { error, fail, redirect } from '@sveltejs/kit';
import { ApiError, transactions, type TransactionFilters } from '$lib/api/client';
import type { Actions, PageServerLoad } from './$types';

function filtersFromUrl(url: URL): TransactionFilters {
  const sp = url.searchParams;
  return {
    search: sp.get('search') ?? undefined,
    status: sp.get('status') ?? undefined,
    book_id: sp.get('book_id') ?? undefined,
    start_date: sp.get('start_date') ?? undefined,
    end_date: sp.get('end_date') ?? undefined,
    include_low_amount: sp.get('include_low_amount') === 'true',
    page: Number(sp.get('page') ?? 1) || 1,
    size: Number(sp.get('size') ?? 20) || 20
  };
}

export const load: PageServerLoad = async ({ url, fetch }) => {
  const filters = filtersFromUrl(url);
  try {
    const result = await transactions.list(fetch, filters);
    return { result, filters, currentSearch: url.search };
  } catch (e) {
    if (e instanceof ApiError && e.status === 403) {
      throw error(403, 'Tu n’as pas la permission de voir les transactions.');
    }
    throw error(500, 'Impossible de charger les transactions.');
  }
};

export const actions: Actions = {
  /** Re-trigger the delivery email for a SUCCESS transaction. */
  resend: async ({ url, request, fetch }) => {
    const data = await request.formData();
    const id = String(data.get('id') ?? '').trim();
    if (!id) return fail(400, { error: 'ID manquant.' });
    try {
      await transactions.resend(fetch, id);
    } catch (e) {
      if (e instanceof ApiError) {
        return fail(e.status, {
          error:
            e.status === 400
              ? 'Cette transaction n’est pas éligible au renvoi (status incorrect).'
              : e.message
        });
      }
      throw e;
    }
    // Stay on the same filtered view.
    throw redirect(303, `/admin/transactions${url.search}`);
  },

  /** Manually verify a payment by provider tx id (sync against Kkiapay). */
  sync: async ({ url, request, fetch }) => {
    const data = await request.formData();
    const id = String(data.get('id') ?? '').trim();
    const provider_tx_id = String(data.get('provider_tx_id') ?? '').trim();
    if (!id || !provider_tx_id) {
      return fail(400, { error: 'ID transaction et provider_tx_id requis.' });
    }
    try {
      await transactions.sync(fetch, id, { provider_tx_id });
    } catch (e) {
      if (e instanceof ApiError) {
        return fail(e.status, {
          error:
            e.status === 409
              ? 'Cet identifiant fournisseur est déjà associé à une autre transaction.'
              : e.status === 404
                ? 'Transaction introuvable.'
                : e.message
        });
      }
      throw e;
    }
    throw redirect(303, `/admin/transactions${url.search}`);
  }
};
