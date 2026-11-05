/**
 * The logo mark lives in components/LogoMark.svelte; the favicon and the
 * home-screen icon are static copies of its "day" version. These checks keep
 * the copies, the page links and the colour tokens in sync.
 */
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { PHASE_STARTS } from './timeOfDay';

const read = (path: string) => readFileSync(fileURLToPath(new URL(path, import.meta.url)), 'utf8');
const exists = (path: string) => existsSync(fileURLToPath(new URL(path, import.meta.url)));

const mark = read('../components/LogoMark.svelte');
const tokens = read('../styles/tokens.css');
const favicon = read('../../public/favicon.svg');
const appleSource = read('../../scripts/apple-touch-icon.svg');
const indexHtml = read('../../index.html');

/** Every `d="…"` path of a file. */
const paths = (text: string) => [...text.matchAll(/\sd="([^"]+)"/g)].map((m) => m[1]);
const token = (name: string) => tokens.match(new RegExp(`--${name}:\\s*(#[0-9a-fA-F]{6})`))?.[1];

describe('brand icons', () => {
  it('are linked from the page and exist', () => {
    expect(indexHtml).toContain('rel="icon" href="./favicon.svg"');
    expect(indexHtml).toContain('rel="apple-touch-icon" href="./apple-touch-icon.png"');
    expect(exists('../../public/favicon.svg')).toBe(true);
    expect(exists('../../public/apple-touch-icon.png')).toBe(true);
  });

  it('copy the shapes of the logo mark', () => {
    const shapes = paths(mark);
    expect(shapes).toHaveLength(4);
    for (const icon of [favicon, appleSource]) {
      expect(paths(icon)).toEqual(shapes);
    }
  });

  it('use the day lens gradient of the tokens', () => {
    for (const n of [1, 2, 3]) {
      const colour = token(`logo-lens-day-${n}`);
      expect(colour).toBeDefined();
      expect(favicon).toContain(`stop-color="${colour}"`);
      expect(appleSource).toContain(`stop-color="${colour}"`);
    }
  });

  it('define a lens gradient for every phase of the day', () => {
    for (const [phase] of PHASE_STARTS) {
      for (const n of [1, 2, 3]) {
        expect(token(`logo-lens-${phase}-${n}`), `${phase}-${n}`).toBeDefined();
      }
    }
  });
});
