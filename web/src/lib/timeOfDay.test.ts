import { describe, expect, it } from 'vitest';
import { PHASE_STARTS, dayPhase, localHour } from './timeOfDay';

describe('localHour', () => {
  it('reads the hour in the given timezone', () => {
    const now = new Date('2026-01-15T05:30:00Z');
    expect(localHour(now, 'Europe/Paris')).toBe(6);
    expect(localHour(now, 'UTC')).toBe(5);
  });

  it('follows summer time', () => {
    expect(localHour(new Date('2026-07-15T05:30:00Z'), 'Europe/Paris')).toBe(7);
  });

  it('returns 0 at midnight, not 24', () => {
    expect(localHour(new Date('2026-01-15T23:00:00Z'), 'Europe/Paris')).toBe(0);
  });
});

describe('dayPhase', () => {
  const paris = (iso: string) => dayPhase(new Date(iso), 'Europe/Paris');

  it('switches at the phase boundaries (winter, UTC+1)', () => {
    expect(paris('2026-01-15T04:59:00Z')).toBe('night'); // 05:59
    expect(paris('2026-01-15T05:00:00Z')).toBe('dawn'); // 06:00
    expect(paris('2026-01-15T07:59:00Z')).toBe('dawn'); // 08:59
    expect(paris('2026-01-15T08:00:00Z')).toBe('day'); // 09:00
    expect(paris('2026-01-15T15:59:00Z')).toBe('day'); // 16:59
    expect(paris('2026-01-15T16:00:00Z')).toBe('dusk'); // 17:00
    expect(paris('2026-01-15T18:59:00Z')).toBe('dusk'); // 19:59
    expect(paris('2026-01-15T19:00:00Z')).toBe('night'); // 20:00
    expect(paris('2026-01-15T23:30:00Z')).toBe('night'); // 00:30
  });

  it('depends on the timezone', () => {
    const now = new Date('2026-01-15T08:30:00Z');
    expect(dayPhase(now, 'Europe/Paris')).toBe('day'); // 09:30
    expect(dayPhase(now, 'UTC')).toBe('dawn'); // 08:30
  });

  it('lists the phases in chronological order', () => {
    const starts = PHASE_STARTS.map(([, hour]) => hour);
    expect([...starts].sort((a, b) => a - b)).toEqual(starts);
    expect(PHASE_STARTS.map(([id]) => id)).toEqual(['dawn', 'day', 'dusk', 'night']);
  });
});
