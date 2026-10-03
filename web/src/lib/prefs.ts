/**
 * Per-device preferences (language, last massif) in localStorage.
 * Storage can be unavailable (private mode, blocked cookies): every access is
 * guarded and the app works without it.
 */
const PREFIX = 'bluebird:';

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
