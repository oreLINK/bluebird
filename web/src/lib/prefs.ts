/**
 * Per-device preferences (language, appearance, place, filter) in localStorage.
 * Storage can be unavailable (private mode, blocked cookies): every access is
 * guarded and the app works without it.
 */
const PREFIX = 'bluebird:';

/** Preferences the site writes (shown and deleted on the privacy page). */
export const PREF_KEYS = ['locale', 'theme', 'geo', 'filter'] as const;

export function readPref(key: string): string | null {
  try {
    return window.localStorage.getItem(PREFIX + key);
  } catch {
    return null;
  }
}

export function writePref(key: string, value: string): void {
  try {
    window.localStorage.setItem(PREFIX + key, value);
  } catch {
    // Preference simply isn't remembered.
  }
}

/** Keys (without the prefix) of the preferences stored on this device. */
export function storedPrefs(): string[] {
  try {
    const keys: string[] = [];
    for (let i = 0; i < window.localStorage.length; i++) {
      const key = window.localStorage.key(i);
      if (key?.startsWith(PREFIX)) keys.push(key.slice(PREFIX.length));
    }
    return keys.sort();
  } catch {
    return [];
  }
}

/** Delete every preference of the site (only its own `bluebird:` keys); returns how many. */
export function clearPrefs(): number {
  const keys = storedPrefs();
  try {
    for (const key of keys) window.localStorage.removeItem(PREFIX + key);
  } catch {
    return 0;
  }
  return keys.length;
}
