/**
 * Framework-free i18n helpers (unit-tested). The reactive store lives in
 * `i18n.svelte.ts`.
 *
 * - UI strings: `fr.json` / `en.json` (keys must match; a test checks it).
 * - Content strings (massif, KPI, tile and driver labels) come from the YAML
 *   configuration as `{ fr, en }` objects and are read with `pickLocalized`.
 */
import en from './en.json';
import es from './es.json';
import fr from './fr.json';

export const LOCALES = ['fr', 'en', 'es'] as const;
export type Locale = (typeof LOCALES)[number];
export type MessageKey = keyof typeof fr;
export type Localized = Record<Locale, string>;

export const dictionaries: Record<Locale, Record<MessageKey, string>> = { fr, en, es };

/** Each language named in itself (endonym), the same in every UI language. */
export const LOCALE_NAMES: Record<Locale, string> = {
  fr: 'Français',
  en: 'English',
  es: 'Español',
};

/** Flag shown for each language (country drawn by components/Flag.svelte). */
export type FlagCountry = 'fr' | 'gb' | 'es';
export const LOCALE_FLAGS: Record<Locale, FlagCountry> = { fr: 'fr', en: 'gb', es: 'es' };

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

/** A localized text built language by language (`text(locale)` for every locale). */
export function localizedFrom(text: (locale: Locale) => string): Localized {
  return Object.fromEntries(LOCALES.map((locale) => [locale, text(locale)])) as Localized;
}

/** The same text in every language (proper names, empty labels). */
export function sameInAll(text: string): Localized {
  return localizedFrom(() => text);
}

export function pickLocalized(text: Partial<Localized> | null | undefined, locale: Locale): string {
  if (!text) return '';
  return text[locale] ?? text.en ?? text.fr ?? '';
}
