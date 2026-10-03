import { describe, expect, it } from 'vitest';
import {
  formatDriver,
  formatLongDate,
  formatOdds,
  formatPercent,
  formatTime,
  formatWindow,
} from './format';

const nbsp = (s: string) => s.replace(/[  ]/g, ' ');

describe('format', () => {
  it('formats percentages per locale', () => {
    expect(nbsp(formatPercent(0.724, 'fr'))).toBe('72 %');
    expect(formatPercent(0.724, 'en')).toBe('72%');
  });

  it('formats decimal odds', () => {
    expect(formatOdds(0.5, 'en')).toBe('2.00');
    expect(formatOdds(0.8, 'fr')).toBe('1,25');
    expect(formatOdds(0, 'en')).toBe('—');
    expect(formatOdds(0.001, 'en')).toBe('99.00');
  });

  it('formats driver values with units and decimals', () => {
    expect(nbsp(formatDriver(12.345, 'fr', 'cm', 1) ?? '')).toBe('12,3 cm');
    expect(formatDriver(91, 'en')).toBe('91');
    expect(formatDriver(null, 'en', 'cm')).toBeNull();
  });

  it('formats dates and times in the massif timezone', () => {
    expect(formatLongDate('2027-01-15', 'fr')).toBe('vendredi 15 janvier');
    expect(formatLongDate('2027-01-15', 'en')).toBe('Friday 15 January');
    expect(formatTime('2027-01-15T04:32:00Z', 'fr', 'Europe/Paris')).toBe('05:32');
  });

  it('shows the day only when a window spans midnight', () => {
    expect(
      formatWindow('2027-01-15T08:00:00+01:00', '2027-01-15T17:00:00+01:00', 'fr', 'Europe/Paris'),
    ).toBe('08:00 → 17:00');
    expect(
      formatWindow('2027-01-14T22:00:00+01:00', '2027-01-15T09:00:00+01:00', 'en', 'Europe/Paris'),
    ).toBe('Thu 22:00 → Fri 09:00');
  });
});
