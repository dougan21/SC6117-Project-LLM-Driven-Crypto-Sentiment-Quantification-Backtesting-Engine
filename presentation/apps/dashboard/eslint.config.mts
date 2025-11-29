import js from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';
import pluginReact from 'eslint-plugin-react';
import { defineConfig } from 'eslint/config';

export default defineConfig([
    {
        ignores: [
            '.next/**',
            'dist/**',
            'node_modules/**',
            '**/*.mjs',
            '**/*.cjs',
        ],
    },
    {
        files: ['**/*.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
        languageOptions: {
            globals: { ...globals.browser, ...globals.node },
            ecmaVersion: 'latest',
            sourceType: 'module',
        },
    },
    {
        files: ['**/*.ts', '**/*.tsx'],
        languageOptions: {
            parser: tseslint.parser,
            parserOptions: {
                ecmaVersion: 'latest',
                sourceType: 'module',
                ecmaFeatures: {
                    jsx: true,
                },
                project: './tsconfig.json',
                tsconfigRootDir: import.meta.dirname,
            },
            globals: globals.browser,
        },
        ...tseslint.configs.recommended[0],
    },
    {
        files: ['**/*.{jsx,tsx}'],
        languageOptions: {
            parser: tseslint.parser,
            parserOptions: {
                ecmaVersion: 'latest',
                sourceType: 'module',
                ecmaFeatures: {
                    jsx: true,
                },
                project: './tsconfig.json',
                tsconfigRootDir: import.meta.dirname,
            },
            globals: globals.browser,
        },
        plugins: { react: pluginReact },
        rules: {
            ...pluginReact.configs.flat.recommended.rules,
            'react/jsx-key': 'off',
            'react/display-name': 'off',
            'react/prop-types': 'off',
            'react/no-unescaped-entities': 'off',
        },
    },
]);
