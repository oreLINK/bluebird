/**
 * Reactive i18n store. Reading `i18n.locale`, `i18n.t()` or `i18n.pick()` in a
 * component re-renders it when the language changes.
 */
import { readPref, writePref } from '../prefs';
import {
  type Locale,
  type Localized,
  type MessageKey,
  detectLocale,
  isLocale,
  pickLocalized,
  translate,
} from './core';

function initialLocale(): Locale {
  const stored = readPref('locale');
  if (isLocale(stored)) return stored;
  return detectLocale(typeof navigator === 'undefined' ? [] : navigator.languages);
}

class I18n {
  locale = $state<Locale>(initialLocale());

  setLocale(locale: Locale): void {
    this.locale = locale;
    writePref('locale', locale);
    document.documentElement.lang = locale;
  }

  t = (key: MessageKey, vars?: Record<string, string | number>): string =>
    translate(this.locale, key, vars);

  pick = (text: Partial<Localized> | null | undefined): string => pickLocalized(text, this.locale);
}

export const i18n = new I18n();
