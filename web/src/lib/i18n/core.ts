/**
 * Framework-free i18n helpers (unit-tested). The reactive store lives in
 * `i18n.svelte.ts`.
 *
 * - UI strings: `fr.json` / `en.json` (keys must match; a test checks it).
 * - Content strings (massif, KPI, tile and driver labels) come from the YAML
 *   configuration as `{ fr, en }` objects and are read with `pickLocalized`.
 */
import en from './en.json';
import fr from './fr.json';

export const LOCALES = ['fr', 'en'] as const;
export type Locale = (typeof LOCALES)[number];
export type MessageKey = keyof typeof fr;
export type Localized = Record<Locale, string>;

export const dictionaries: Record<Locale, Record<MessageKey, string>> = { fr, en };

export function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (LOCALES as readonly string[]).includes(value);
}

/** First supported locale among the browser languages; French otherwise. */
export function detectLocale(languages: readonly string[]): Locale {
  for (const language of languages) {
    const base = language.toLowerCase().split('-')[0];
    if (isLocale(base)) return base;
  }
  return 'fr';
}

/** Replace `{name}` placeholders. */
export function interpolate(template: string, vars?: Record<string, string | number>): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in vars ? String(vars[name]) : match,
  );
}

export function translate(
  locale: Locale,
  key: MessageKey,
  vars?: Record<string, string | number>,
): string {
  return interpolate(dictionaries[locale][key] ?? dictionaries.en[key] ?? key, vars);
}

export function pickLocalized(text: Partial<Localized> | null | undefined, locale: Locale): string {
  if (!text) return '';
  return text[locale] ?? text.en ?? text.fr ?? '';
}
