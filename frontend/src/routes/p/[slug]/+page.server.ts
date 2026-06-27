import { error, fail, redirect, type Actions } from '@sveltejs/kit';
import { BACKEND_BASE } from '$lib/server/env';
import { ApiError, pages } from '$lib/api/client';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, fetch }) => {
  try {
    const page = await pages.public(fetch, params.slug);
    return { page };
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      throw error(404, 'Page introuvable.');
    }
    throw error(500, 'Impossible de charger la page.');
  }
};

export const actions: Actions = {
  /**
   * Submitted by the embedded PaymentForm block. Forwards to the backend
   * ``POST /purchases``; on success, redirects to the provider's payment
   * URL so the customer lands directly on the Kkiapay widget.
   *
   * No SvelteKit cookies are forwarded for this call — ``/purchases`` is
   * unauthenticated, the customer doesn't have a session at this stage.
   */
  checkout: async ({ request, fetch, getClientAddress }) => {
    const data = await request.formData();
    const payload = {
      book_id: String(data.get('book_id') ?? '').trim(),
      email: String(data.get('email') ?? '').trim(),
      name: String(data.get('name') ?? '').trim(),
      surname: String(data.get('surname') ?? '').trim(),
      phone: String(data.get('phone') ?? '').trim(),
      country: String(data.get('country') ?? 'Côte d’Ivoire').trim(),
      city: String(data.get('city') ?? '').trim()
    };

    // Minimal client-side guard; backend re-validates strictly.
    for (const k of ['book_id', 'email', 'name', 'surname', 'phone', 'city'] as const) {
      if (!payload[k]) {
        return fail(400, { error: `Champ requis manquant : ${k}.`, form: payload });
      }
    }

    let res: Response;
    try {
      res = await fetch(`${BACKEND_BASE}/purchases`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          // Pass the real client IP through to the backend so the
          // Customer record carries it rather than the SvelteKit pod IP.
          'x-forwarded-for': getClientAddress()
        },
        body: JSON.stringify(payload)
      });
    } catch {
      return fail(502, { error: 'Service de paiement indisponible.', form: payload });
    }

    if (res.status === 429) {
      return fail(429, {
        error: 'Trop de tentatives. Réessaye dans une minute.',
        form: payload
      });
    }
    if (!res.ok) {
      const body = await res.text().catch(() => '');
      return fail(res.status, {
        error: `Erreur paiement (${res.status}). ${body}`.slice(0, 300),
        form: payload
      });
    }

    const json = (await res.json()) as { payment_url: string };
    if (!json.payment_url) {
      return fail(502, { error: 'Réponse invalide du fournisseur.', form: payload });
    }
    throw redirect(303, json.payment_url);
  }
};
