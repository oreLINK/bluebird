import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { PREF_KEYS, clearPrefs, readPref, storedPrefs, writePref } from './prefs';

/** A minimal in-memory localStorage. */
function fakeStorage(): Storage {
  const map = new Map<string, string>();
  return {
    get length() {
      return map.size;
    },
    key: (i: number) => [...map.keys()][i] ?? null,
    getItem: (k: string) => map.get(k) ?? null,
    setItem: (k: string, v: string) => void map.set(k, v),
    removeItem: (k: string) => void map.delete(k),
    clear: () => map.clear(),
  };
}

describe('prefs', () => {
  beforeEach(() => {
    (globalThis as { window?: unknown }).window = { localStorage: fakeStorage() };
  });
  afterEach(() => {
    delete (globalThis as { window?: unknown }).window;
  });

  it('lists only the site preferences', () => {
    writePref('locale', 'es');
    writePref('theme', 'dark');
    window.localStorage.setItem('other-site', 'x');
    expect(storedPrefs()).toEqual(['locale', 'theme']);
  });

  it('deletes every site preference and nothing else', () => {
    for (const key of PREF_KEYS) writePref(key, 'v');
    window.localStorage.setItem('other-site', 'x');
    expect(clearPrefs()).toBe(4);
    expect(storedPrefs()).toEqual([]);
    expect(readPref('locale')).toBeNull();
    expect(window.localStorage.getItem('other-site')).toBe('x');
  });

  it('works without storage', () => {
    (globalThis as { window?: unknown }).window = {
      get localStorage(): Storage {
        throw new Error('blocked');
      },
    };
    expect(storedPrefs()).toEqual([]);
    expect(clearPrefs()).toBe(0);
    expect(readPref('locale')).toBeNull();
  });
});
