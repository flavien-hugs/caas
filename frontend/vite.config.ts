import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

// Vitest config is declared via the `test` property; Vite 6 typings don't
// know about it but Vitest 2's plugin picks it up at runtime regardless.
export default defineConfig({
  plugins: [tailwindcss(), sveltekit()],
  server: {
    port: 5173,
    strictPort: false
  },
  // @ts-expect-error — Vitest extends UserConfig at runtime.
  test: {
    include: ['src/**/*.{test,spec}.{js,ts}'],
    environment: 'jsdom',
    globals: true
  }
});
