import { describe, expect, it } from 'vitest';
import { detectLocale, dictionaries, interpolate, pickLocalized, translate } from './core';

describe('i18n', () => {
  it('has the same keys in every language', () => {
    expect(Object.keys(dictionaries.en).sort()).toEqual(Object.keys(dictionaries.fr).sort());
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
  });

  it('interpolates placeholders and keeps unknown ones', () => {
    expect(interpolate('{a} and {b}', { a: 1 })).toBe('1 and {b}');
    expect(translate('en', 'tile.seeAll', { count: 18 })).toBe('See all 18 resorts');
  });

  it('picks localized content with an English fallback', () => {
    expect(pickLocalized({ fr: 'Neige', en: 'Snow' }, 'fr')).toBe('Neige');
    expect(pickLocalized({ en: 'Snow' }, 'fr')).toBe('Snow');
    expect(pickLocalized(undefined, 'fr')).toBe('');
  });
});
