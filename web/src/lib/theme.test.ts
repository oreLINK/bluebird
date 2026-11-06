import { describe, expect, it } from 'vitest';
import { THEMES, THEME_ICONS, applyTheme, parseTheme } from './theme';

const root = () => ({ dataset: {} as DOMStringMap });
const metas = () => [
  { content: '#0a4aa6', media: '(prefers-color-scheme: light)', dataset: {} as DOMStringMap },
  { content: '#020817', media: '(prefers-color-scheme: dark)', dataset: {} as DOMStringMap },
];

describe('theme', () => {
  it('defaults to the system setting for a missing or unknown preference', () => {
    expect(parseTheme(null)).toBe('system');
    expect(parseTheme('sepia')).toBe('system');
    expect(parseTheme('dark')).toBe('dark');
  });

  it('has an icon for every choice', () => {
    expect(THEMES.map((t) => THEME_ICONS[t])).toEqual(['sun-moon', 'sun', 'moon']);
  });

  it('forces a mode with data-theme and removes it for the system setting', () => {
    const r = root();
    applyTheme('dark', r);
    expect(r.dataset.theme).toBe('dark');
    applyTheme('light', r);
    expect(r.dataset.theme).toBe('light');
    applyTheme('system', r);
    expect(r.dataset.theme).toBeUndefined();
  });

  it('colours the browser bar like the forced mode, and restores it for the system', () => {
    const r = root();
    const m = metas();
    applyTheme('dark', r, m);
    expect(m.map((x) => x.content)).toEqual(['#020817', '#020817']);
    applyTheme('light', r, m);
    expect(m.map((x) => x.content)).toEqual(['#0a4aa6', '#0a4aa6']);
    applyTheme('system', r, m);
    expect(m.map((x) => x.content)).toEqual(['#0a4aa6', '#020817']);
  });
});
