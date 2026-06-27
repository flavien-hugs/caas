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
      // Surface Svelte compiler warnings (svelte-check stays the canonical
      // compile check; this is a secondary signal in eslint).
      'svelte/valid-compile': 'warn'
    }
  },
  {
    // UI primitives forward arbitrary HTML attributes via ``...rest`` in
    // ``$props()`` — intentional, and these are never compiled as custom
    // elements, so the ``custom_element_props_identifier`` warning is a false
    // positive here. svelte-check still validates them.
    files: ['src/lib/components/ui/**/*.svelte'],
    rules: {
      'svelte/valid-compile': 'off'
    }
  },
  {
    ignores: ['build/', 'dist/', '.svelte-kit/', 'node_modules/', 'src/lib/api/schema.gen.ts']
  }
);
