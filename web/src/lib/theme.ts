/**
 * Appearance (pure helpers, unit-tested): `system` follows the device setting,
 * `light` and `dark` force a mode by setting `data-theme` on <html>, which the
 * tokens of styles/tokens.css already honour. Remembered per device
 * (preference `theme`); index.html applies it before the first paint.
 */
export const THEMES = ['system', 'light', 'dark'] as const;
export type ThemeChoice = (typeof THEMES)[number];

export const DEFAULT_THEME: ThemeChoice = 'system';

/** Icon of the header button and of each option (components/Icon.svelte). */
export const THEME_ICONS: Record<ThemeChoice, string> = {
  system: 'sun-moon',
  light: 'sun',
  dark: 'moon',
};

export function isTheme(value: unknown): value is ThemeChoice {
  return typeof value === 'string' && (THEMES as readonly string[]).includes(value);
}

/** A stored preference, or the default when missing or unknown. */
export function parseTheme(value: string | null | undefined): ThemeChoice {
  return isTheme(value) ? value : DEFAULT_THEME;
}

interface ThemeRoot {
  dataset: DOMStringMap;
}

interface ThemeColorMeta {
  content: string;
  media: string;
  dataset: DOMStringMap;
}

/**
 * Apply a choice: `data-theme` on the root (removed for `system`), and the
 * browser bar colour (`<meta name="theme-color">`, one per scheme): forced
 * modes use their scheme's colour for both metas, `system` restores them.
 */
export function applyTheme(choice: ThemeChoice, root: ThemeRoot, metas: ThemeColorMeta[] = []): void {
  if (choice === 'system') delete root.dataset.theme;
  else root.dataset.theme = choice;
  for (const meta of metas) meta.dataset.color ??= meta.content;
  const colorOf = (scheme: string) => metas.find((m) => m.media.includes(scheme))?.dataset.color;
  for (const meta of metas) {
    const forced = choice === 'system' ? undefined : colorOf(choice);
    meta.content = forced ?? meta.dataset.color ?? meta.content;
  }
}
