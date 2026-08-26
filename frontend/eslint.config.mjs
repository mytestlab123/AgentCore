import js from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      // Provider errors can contain runtime identifiers; the UI emits a generic error.
      'preserve-caught-error': 'off',
    },
  },
  {
    files: ['e2e/**/*.mjs'],
    languageOptions: {
      globals: globals.node,
    },
  },
);
