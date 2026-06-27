import { BACKEND_BASE } from '$lib/server/env';
import type { CurrentUser } from '$lib/server/session';

/**
 * Minimal typed wrapper around `fetch` that targets the backend.
 *
 * We don't pull in `openapi-fetch` yet — Chunk B will swap this for the
 * generated client. For Chunk A (auth + dashboard) the surface is small
 * enough that hand-rolled types are clearer than codegen.
 *
 * Always pass SvelteKit's `event.fetch` so `handleFetch` in
 * `hooks.server.ts` forwards the session cookie.
 */

type FetchFn = typeof fetch;

interface JsonOpts {
  fetch: FetchFn;
  body?: unknown;
  signal?: AbortSignal;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly body: unknown = undefined
  ) {
    super(message);
  }
}

async function request<T>(method: string, path: string, opts: JsonOpts): Promise<T> {
  const res = await opts.fetch(`${BACKEND_BASE}${path}`, {
    method,
    headers: { 'content-type': 'application/json' },
    body: opts.body == null ? undefined : JSON.stringify(opts.body),
    signal: opts.signal
  });

  if (res.status === 204) return undefined as T;
  const ct = res.headers.get('content-type') ?? '';
  const payload = ct.includes('application/json') ? await res.json() : await res.text();

  if (!res.ok) {
    throw new ApiError(
      typeof payload === 'object' && payload && 'detail' in payload
        ? String((payload as { detail: unknown }).detail)
        : `${method} ${path} failed (${res.status})`,
      res.status,
      payload
    );
  }
  return payload as T;
}

export const api = {
  get: <T>(path: string, opts: JsonOpts) => request<T>('GET', path, opts),
  post: <T>(path: string, opts: JsonOpts) => request<T>('POST', path, opts),
  put: <T>(path: string, opts: JsonOpts) => request<T>('PUT', path, opts),
  patch: <T>(path: string, opts: JsonOpts) => request<T>('PATCH', path, opts),
  del: <T>(path: string, opts: JsonOpts) => request<T>('DELETE', path, opts)
};

// --- typed endpoints used by Chunk A foundation -----------------------------

export interface AuthMe {
  username: string;
  role: string;
}

export const auth = {
  login: (fetch: FetchFn, username: string, password: string) =>
    api.post<AuthMe>('/auth/login', { fetch, body: { username, password } }),
  me: (fetch: FetchFn) => api.get<AuthMe>('/auth/me', { fetch }),
  logout: (fetch: FetchFn) => api.post<void>('/auth/logout', { fetch })
};

export interface DashboardStats {
  total_revenue: number;
  successful_sales: number;
  pending_transactions: number;
  failed_transactions: number;
  total_transactions: number;
}

export const dashboard = {
  stats: (fetch: FetchFn) => api.get<DashboardStats>('/admin/dashboard/stats', { fetch })
};

// --- pages (Chunk B) --------------------------------------------------------

export interface ApiBlock {
  id: string;
  type: string;
  props: Record<string, unknown>;
}

export interface ApiPage {
  id: string;
  slug: string;
  title: string;
  blocks: ApiBlock[];
  status: 'draft' | 'published';
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

export interface PublicPage {
  slug: string;
  title: string;
  blocks: ApiBlock[];
  published_at: string | null;
}

export const pages = {
  list: (fetch: FetchFn) => api.get<ApiPage[]>('/admin/pages', { fetch }),
  get: (fetch: FetchFn, id: string) => api.get<ApiPage>(`/admin/pages/${id}`, { fetch }),
  create: (fetch: FetchFn, body: { slug: string; title: string }) =>
    api.post<ApiPage>('/admin/pages', { fetch, body }),
  update: (
    fetch: FetchFn,
    id: string,
    body: { slug?: string; title?: string; blocks?: ApiBlock[] }
  ) => api.patch<ApiPage>(`/admin/pages/${id}`, { fetch, body }),
  publish: (fetch: FetchFn, id: string) =>
    api.post<ApiPage>(`/admin/pages/${id}/publish`, { fetch }),
  unpublish: (fetch: FetchFn, id: string) =>
    api.post<ApiPage>(`/admin/pages/${id}/unpublish`, { fetch }),
  remove: (fetch: FetchFn, id: string) => api.del<void>(`/admin/pages/${id}`, { fetch }),
  public: (fetch: FetchFn, slug: string) => api.get<PublicPage>(`/pages/${slug}`, { fetch })
};

// --- users -----------------------------------------------------------------

export type ApiRole = 'super_admin' | 'admin' | 'operator' | 'reader';

export interface ApiUser {
  id: string;
  username: string;
  role: string;
  created_at: string;
  updated_at: string;
}

export interface CreateUserBody {
  username: string;
  password: string;
  role: ApiRole;
}

export interface UpdateUserBody {
  username?: string;
  password?: string;
  role?: ApiRole;
}

export const users = {
  list: (fetch: FetchFn) => api.get<ApiUser[]>('/admin/users', { fetch }),
  get: (fetch: FetchFn, id: string) => api.get<ApiUser>(`/admin/users/${id}`, { fetch }),
  create: (fetch: FetchFn, body: CreateUserBody) =>
    api.post<ApiUser>('/admin/users', { fetch, body }),
  update: (fetch: FetchFn, id: string, body: UpdateUserBody) =>
    api.patch<ApiUser>(`/admin/users/${id}`, { fetch, body }),
  remove: (fetch: FetchFn, id: string) => api.del<void>(`/admin/users/${id}`, { fetch })
};

// --- runtime configuration (settings) --------------------------------------

export type ConfigSectionName = 'general' | 'smtp' | 'kkiapay' | 'cinetpay' | 'sms';

export interface SectionConfig {
  /** Non-secret effective values (DB over env). */
  values: Record<string, unknown>;
  /** Per-secret-field flag: true when a value is configured. */
  secrets: Record<string, boolean>;
}

export type AllSettings = Record<ConfigSectionName, SectionConfig>;

export const settings = {
  all: (fetch: FetchFn) => api.get<AllSettings>('/admin/settings', { fetch }),
  section: (fetch: FetchFn, section: ConfigSectionName) =>
    api.get<SectionConfig>(`/admin/settings/${section}`, { fetch }),
  update: (fetch: FetchFn, section: ConfigSectionName, values: Record<string, unknown>) =>
    api.put<SectionConfig>(`/admin/settings/${section}`, { fetch, body: values }),
  testSmtp: (fetch: FetchFn, to: string) =>
    api.post<void>('/admin/settings/smtp/test', { fetch, body: { to } }),
  testSms: (fetch: FetchFn, to: string, body?: string) =>
    api.post<void>('/admin/settings/sms/test', { fetch, body: { to, body } })
};

// --- transactions ----------------------------------------------------------

export interface ApiTransaction {
  id: string;
  book_id: string | null;
  user_email: string;
  user_name: string | null;
  user_phone: string | null;
  user_country: string | null;
  user_city: string | null;
  amount: number;
  currency: string;
  status: string;
  transaction_id: string | null;
  created_at: string;
}

export interface PaginatedTransactions {
  items: ApiTransaction[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface TransactionFilters {
  search?: string;
  status?: string;
  book_id?: string;
  start_date?: string;
  end_date?: string;
  include_low_amount?: boolean;
  page?: number;
  size?: number;
}

function buildQuery(filters: TransactionFilters): string {
  const sp = new URLSearchParams();
  if (filters.search) sp.set('search', filters.search);
  if (filters.status) sp.set('status', filters.status);
  if (filters.book_id) sp.set('book_id', filters.book_id);
  if (filters.start_date) sp.set('start_date', filters.start_date);
  if (filters.end_date) sp.set('end_date', filters.end_date);
  if (filters.include_low_amount) sp.set('include_low_amount', 'true');
  if (filters.page) sp.set('page', String(filters.page));
  if (filters.size) sp.set('size', String(filters.size));
  const s = sp.toString();
  return s ? `?${s}` : '';
}

export interface SyncTransactionBody {
  provider_tx_id: string;
}

export interface CallbackResponse {
  purchase_id: string;
  status: string;
  confirmed: boolean;
  delivered: boolean;
}

export interface ResendResponse {
  purchase_id: string;
  delivered: boolean;
}

export const transactions = {
  list: (fetch: FetchFn, filters: TransactionFilters = {}) =>
    api.get<PaginatedTransactions>(`/admin/transactions${buildQuery(filters)}`, { fetch }),
  resend: (fetch: FetchFn, id: string) =>
    api.post<ResendResponse>(`/admin/transactions/${id}/resend`, { fetch }),
  sync: (fetch: FetchFn, id: string, body: SyncTransactionBody) =>
    api.post<CallbackResponse>(`/admin/transactions/${id}/sync`, { fetch, body }),
  exportUrl: (filters: TransactionFilters = {}) =>
    `/admin/transactions/export.xlsx${buildQuery(filters)}`
};

export function currentUserFrom(me: AuthMe): CurrentUser {
  return { username: me.username, role: me.role };
}
