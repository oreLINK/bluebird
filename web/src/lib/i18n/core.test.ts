import { describe, expect, it } from 'vitest';
import {
  LOCALES,
  LOCALE_FLAGS,
  LOCALE_NAMES,
  detectLocale,
  dictionaries,
  interpolate,
  localizedFrom,
  pickLocalized,
  sameInAll,
  translate,
} from './core';

describe('i18n', () => {
  it('has the same keys in every language', () => {
    const keys = Object.keys(dictionaries.fr).sort();
    for (const locale of LOCALES) expect(Object.keys(dictionaries[locale]).sort()).toEqual(keys);
  });

  it('keeps the same placeholders in every language', () => {
    const placeholders = (text: string) => (text.match(/\{\w+\}/g) ?? []).sort();
    for (const [key, text] of Object.entries(dictionaries.fr)) {
      for (const locale of LOCALES) {
        const other = dictionaries[locale][key as keyof typeof dictionaries.fr];
        expect(placeholders(other), `${locale} ${key}`).toEqual(placeholders(text));
      }
    }
  });

  it('has no empty translation', () => {
    for (const dict of Object.values(dictionaries)) {
      for (const value of Object.values(dict)) expect(value.trim()).not.toBe('');
    }
  });

  it('detects the browser language', () => {
    expect(detectLocale(['en-US', 'fr'])).toBe('en');
    expect(detectLocale(['de-DE', 'fr-CA'])).toBe('fr');
    expect(detectLocale(['de-DE'])).toBe('fr');
    expect(detectLocale(['es-ES', 'en'])).toBe('es');
    expect(detectLocale(['ca-ES', 'es-MX'])).toBe('es');
  });

  it('gives every language a name and a flag', () => {
    for (const locale of LOCALES) {
      expect(LOCALE_NAMES[locale]).toBeTruthy();
      expect(['fr', 'gb', 'es']).toContain(LOCALE_FLAGS[locale]);
    }
  });

  it('builds localized texts for every language', () => {
    expect(localizedFrom((l) => l.toUpperCase())).toEqual({ fr: 'FR', en: 'EN', es: 'ES' });
    expect(sameInAll('Font-Romeu')).toEqual({ fr: 'Font-Romeu', en: 'Font-Romeu', es: 'Font-Romeu' });
    expect(translate('es', 'tile.seeAll', { count: 18 })).toBe('Ver las 18 estaciones');
  });

  it('names the current language on the flag button', () => {
    expect(translate('fr', 'language.open', { language: LOCALE_NAMES.fr })).toBe(
      'Choisir la langue (actuelle : Français)',
    );
    expect(translate('en', 'language.open', { language: LOCALE_NAMES.en })).toBe(
      'Choose the language (current: English)',
    );
  });

  it('interpolates placeholders and keeps unknown ones', () => {
    expect(interpolate('{a} and {b}', { a: 1 })).toBe('1 and {b}');
    expect(translate('en', 'tile.seeAll', { count: 18 })).toBe('See all 18 resorts');
  });

  it('picks localized content with an English fallback', () => {
    expect(pickLocalized({ fr: 'Neige', en: 'Snow', es: 'Snow' }, 'fr')).toBe('Neige');
    expect(pickLocalized({ en: 'Snow', es: 'Snow' }, 'fr')).toBe('Snow');
    expect(pickLocalized(undefined, 'fr')).toBe('');
  });
});
