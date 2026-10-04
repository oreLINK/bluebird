import { describe, expect, it } from 'vitest';
import {
  formatDate,
  formatDriver,
  formatSeason,
  formatMethod,
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
    expect(formatDate('2025-12-01', 'fr')).toBe('1 déc. 2025');
    expect(formatDate('2026-05-01', 'en')).toBe('1 May 2026');
    expect(formatSeason('2025-12-01', '2026-05-01')).toBe('2025/2026');
    expect(formatSeason('2026-01-01', '2026-04-30')).toBe('2026');
    const tomorrow = ['2027-01-16T09:00:00+01:00', '2027-01-16T17:00:00+01:00'] as const;
    expect(formatWindow(...tomorrow, 'fr', 'Europe/Paris', '2027-01-15')).toBe('sam. 09:00 → 17:00');
    expect(formatWindow(...tomorrow, 'fr', 'Europe/Paris', '2027-01-16')).toBe('09:00 → 17:00');
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

describe('formatMethod', () => {
  it('fills placeholders with locale-formatted params and keeps unknown ones', () => {
    const params = { threshold_cm: 15.0, thaw_temp_c: 0.5, window_start: '08:00' };
    expect(formatMethod('{threshold_cm} cm, {thaw_temp_c} °C, {window_start}', params, 'fr')).toBe(
      '15 cm, 0,5 °C, 08:00',
    );
    expect(formatMethod('{missing}', params, 'en')).toBe('{missing}');
  });
});
