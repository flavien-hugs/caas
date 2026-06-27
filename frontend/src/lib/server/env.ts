import { env } from '$env/dynamic/private';

/**
 * Base URL of the backend API.
 *
 * Read at runtime via `$env/dynamic/private` (not inlined at build), so the
 * same Docker image works across environments — just set `BACKEND_BASE` in
 * the container. Server-side only ($lib/server/*).
 */
export const BACKEND_BASE = env.BACKEND_BASE ?? 'http://localhost:8080';
