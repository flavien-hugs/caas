// See https://svelte.dev/docs/kit/types#app
import type { CurrentUser } from '$lib/server/session';

declare global {
  namespace App {
    interface Locals {
      user: CurrentUser | null;
    }
    interface PageData {
      user?: CurrentUser | null;
    }
    // interface Error {}
    // interface Platform {}
  }
}

export {};
