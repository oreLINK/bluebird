import { describe, expect, it } from 'vitest';
import type { RankingEntry } from './data';
import { reliability, sharedWindow, splitTop } from './ranking';

const entry = (station_id: string, probability: number, start = 'S', end = 'E'): RankingEntry => ({
  station_id,
  probability,
  confidence: 'high',
  window_start: start,
  window_end: end,
  members: 91,
  drivers: {},
});

describe('ranking helpers', () => {
  it('returns the window shared by every station, or null', () => {
    expect(sharedWindow([entry('a', 0.5), entry('b', 0.4)])).toEqual({ start: 'S', end: 'E' });
    expect(sharedWindow([entry('a', 0.5), entry('b', 0.4, 'X')])).toBeNull();
    expect(sharedWindow([])).toBeNull();
  });

  it('splits the top entries from the rest', () => {
    const ranking = ['a', 'b', 'c', 'd', 'e'];
    expect(splitTop(ranking, 3)).toEqual({ top: ['a', 'b', 'c'], rest: ['d', 'e'] });
    expect(splitTop(ranking.slice(0, 2), 3)).toEqual({ top: ['a', 'b'], rest: [] });
  });

});

describe('reliability', () => {
  const withConfidence = (confidence: 'low' | 'medium' | 'high', members = 91) => ({
    ...entry('x', 0.5),
    confidence,
    members,
  });

  it('averages the station confidences into an index and a level', () => {
    const result = reliability([
      withConfidence('high'),
      withConfidence('high'),
      withConfidence('medium', 80),
      withConfidence('low'),
    ]);
    expect(result?.score).toBeCloseTo(0.625);
    expect(result?.level).toBe('medium');
    expect(result?.counts).toEqual({ high: 2, medium: 1, low: 1 });
    expect(result?.members).toBe(80);
  });

  it('is high when every station agrees and null without data', () => {
    expect(reliability([withConfidence('high')])?.level).toBe('high');
    expect(reliability([])).toBeNull();
  });
});
