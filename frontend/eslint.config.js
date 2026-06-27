import ts from 'typescript-eslint';
import svelte from 'eslint-plugin-svelte';

// Flat config (ESLint 9). N'utilise que les deps déjà présentes
// (typescript-eslint + eslint-plugin-svelte). `flat/prettier` désactive les
// règles de mise en forme qui entrent en conflit avec Prettier (lancé à part).
export default ts.config(
  ...ts.configs.recommended,
  ...svelte.configs['flat/recommended'],
  ...svelte.configs['flat/prettier'],
  {
    files: ['**/*.svelte'],
    languageOptions: {
      parserOptions: {
        parser: ts.parser
      }
    }
  },
  {
    rules: {
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }
      ],
      '@typescript-eslint/no-explicit-any': 'warn',
      // The page builder renders Markdown that is sanitized with DOMPurify
      // (see ``$lib/markdown``) before it reaches ``{@html}``, so this rule
      // would only produce false positives here.
      'svelte/no-at-html-tags': 'off',
      // Surface Svelte compiler warnings without failing the build on the
      // pre-existing UI primitives that spread ``$props()``.
      'svelte/valid-compile': 'warn'
    }
  },
  {
    ignores: ['build/', 'dist/', '.svelte-kit/', 'node_modules/', 'src/lib/api/schema.gen.ts']
  }
);
