import { error } from '@sveltejs/kit';
import { BACKEND_BASE } from '$lib/server/env';
import type { RequestHandler } from './$types';

/**
 * Proxy the Excel export from the backend so the browser can download it
 * with the admin's session cookie attached.
 *
 * SvelteKit's ``event.fetch`` forwards cookies to ``BACKEND_BASE`` via
 * ``hooks.server.ts:handleFetch``; we just need to mirror the response
 * stream and the ``Content-Disposition`` header back to the browser.
 */
export const GET: RequestHandler = async ({ url, fetch }) => {
  const upstream = await fetch(`${BACKEND_BASE}/admin/transactions/export.xlsx${url.search}`, {
    method: 'GET'
  });

  if (upstream.status === 401) throw error(401, 'Session expirée.');
  if (upstream.status === 403) throw error(403, 'Permission refusée.');
  if (!upstream.ok) throw error(upstream.status, 'Export indisponible.');

  return new Response(upstream.body, {
    status: 200,
    headers: {
      'content-type':
        upstream.headers.get('content-type') ??
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'content-disposition':
        upstream.headers.get('content-disposition') ?? 'attachment; filename="transactions.xlsx"'
    }
  });
};
