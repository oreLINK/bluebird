/// <reference types="vitest/config" />
import { fileURLToPath } from 'node:url';
import yaml from '@rollup/plugin-yaml';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';

// The YAML files in ../config are the single source of truth for massifs,
// KPIs, tiles and layout. They are bundled at build time, so changing the
// layout only needs a rebuild (done automatically on every merge into main).
const configDir = fileURLToPath(new URL('../config', import.meta.url));

export default defineConfig({
  // Relative base: the site works from any GitHub Pages sub-path.
  base: './',
  plugins: [svelte(), yaml()],
  resolve: {
    alias: { '@config': configDir },
  },
  server: {
    fs: { allow: ['..'] },
  },
  build: {
    target: 'es2022',
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
});
