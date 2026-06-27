import { error, fail } from '@sveltejs/kit';
import { ApiError, settings, type ConfigSectionName } from '$lib/api/client';
import type { Actions, PageServerLoad } from './$types';

type FieldType = 'string' | 'int' | 'bool' | 'secret';

/**
 * Field metadata per section, mirroring the backend Pydantic schemas
 * (`backend/src/application/config/schemas.py`). Drives form payload building:
 * secrets left blank are omitted (kept server-side), bools/ints are coerced.
 */
const SECTION_FIELDS: Record<ConfigSectionName, { name: string; type: FieldType }[]> = {
  general: [
    { name: 'payment_provider', type: 'string' },
    { name: 'site_url', type: 'string' }
  ],
  smtp: [
    { name: 'host', type: 'string' },
    { name: 'port', type: 'int' },
    { name: 'user', type: 'string' },
    { name: 'password', type: 'secret' },
    { name: 'from_email', type: 'string' }
  ],
  kkiapay: [
    { name: 'public_key', type: 'string' },
    { name: 'private_key', type: 'secret' },
    { name: 'secret_key', type: 'secret' },
    { name: 'sandbox', type: 'bool' }
  ],
  cinetpay: [
    { name: 'site_id', type: 'string' },
    { name: 'api_key', type: 'secret' },
    { name: 'sandbox', type: 'bool' }
  ],
  sms: [
    { name: 'provider_url', type: 'string' },
    { name: 'api_key', type: 'secret' },
    { name: 'sender', type: 'string' }
  ]
};

const SECTIONS = Object.keys(SECTION_FIELDS) as ConfigSectionName[];

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    return { settings: await settings.all(fetch) };
  } catch (e) {
    if (e instanceof ApiError && e.status === 403) {
      throw error(403, 'Tu n’as pas la permission de gérer la configuration.');
    }
    throw error(500, 'Impossible de charger la configuration.');
  }
};

export const actions: Actions = {
  save: async ({ request, fetch }) => {
    const data = await request.formData();
    const section = String(data.get('section') ?? '') as ConfigSectionName;
    if (!SECTIONS.includes(section)) {
      return fail(400, { section, error: 'Section inconnue.' });
    }

    const payload: Record<string, unknown> = {};
    for (const field of SECTION_FIELDS[section]) {
      const raw = data.get(field.name);
      if (field.type === 'bool') {
        payload[field.name] = raw === 'on' || raw === 'true';
        continue;
      }
      const value = raw == null ? '' : String(raw);
      if (field.type === 'secret') {
        if (value) payload[field.name] = value; // blank → keep existing
        continue;
      }
      if (field.type === 'int') {
        payload[field.name] = value === '' ? 0 : Number(value);
        continue;
      }
      payload[field.name] = value;
    }

    try {
      const updated = await settings.update(fetch, section, payload);
      return { saved: section, section: updated };
    } catch (e) {
      if (e instanceof ApiError) {
        return fail(e.status, {
          section,
          error: e.status === 422 ? 'Valeurs invalides.' : e.message
        });
      }
      throw e;
    }
  },

  testSmtp: async ({ request, fetch }) => {
    const data = await request.formData();
    const to = String(data.get('to') ?? '').trim();
    if (!to) return fail(400, { test: 'smtp', error: 'Adresse email requise.' });
    try {
      await settings.testSmtp(fetch, to);
      return { tested: 'smtp', to };
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Échec inattendu.';
      return fail(e instanceof ApiError ? e.status : 500, { test: 'smtp', error: msg });
    }
  },

  testSms: async ({ request, fetch }) => {
    const data = await request.formData();
    const to = String(data.get('to') ?? '').trim();
    const body = String(data.get('body') ?? '').trim() || undefined;
    if (!to) return fail(400, { test: 'sms', error: 'Numéro requis.' });
    try {
      await settings.testSms(fetch, to, body);
      return { tested: 'sms', to };
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Échec inattendu.';
      return fail(e instanceof ApiError ? e.status : 500, { test: 'sms', error: msg });
    }
  }
};
