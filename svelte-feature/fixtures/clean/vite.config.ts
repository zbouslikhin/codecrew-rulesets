import { svelte } from '@sveltejs/vite-plugin-svelte';
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [svelte()],
	resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } }
});
