// Managed by the codecrew 'svelte-feature' ruleset.
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { svelteTesting } from '@testing-library/svelte/vite';
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [svelte(), svelteTesting()],
	resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
	test: { environment: 'jsdom', include: ['src/**/*.test.ts'], includeTaskLocation: true }
});
