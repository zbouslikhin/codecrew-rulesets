// Managed by the codecrew 'svelte-feature' ruleset.
import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import ts from 'typescript-eslint';

export default ts.config(
	// *.generated.ts: machine-written code (e.g. API types), not held to hand-written rules.
	{
		ignores: ['node_modules/', 'dist/', 'build/', '.svelte-kit/', '.codecrew/', '**/*.generated.ts']
	},
	js.configs.recommended,
	...ts.configs.recommended,
	...svelte.configs.recommended,
	{ languageOptions: { globals: { ...globals.browser, ...globals.node } } },
	{
		files: ['**/*.svelte', '**/*.svelte.ts'],
		languageOptions: { parserOptions: { parser: ts.parser, extraFileExtensions: ['.svelte'] } }
	},
	{
		rules: {
			'no-restricted-imports': [
				'error',
				{
					patterns: [
						{
							regex: '^\\.\\./',
							message: "Use the '@/...' alias instead of parent-relative imports."
						}
					]
				}
			]
		}
	},
	{
		// .ts files are covered by the ast-grep rule; .svelte script blocks are covered here.
		files: ['**/*.svelte'],
		rules: {
			'@typescript-eslint/naming-convention': [
				'error',
				{ selector: 'typeAlias', format: ['PascalCase'], prefix: ['T'] }
			]
		}
	}
);
