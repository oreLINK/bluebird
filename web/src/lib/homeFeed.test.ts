import { describe, expect, it } from 'vitest';
import type { Kpi, ResolvedTile, Tile } from './config';
import type { MassifDaily } from './data';
import type { HomePage } from './generated/layout';
import { clockOf, homeFeed, impactOf, reliabilityOf, skiClock, stepFactor } from './homeFeed';

const name = { fr: 'x', en: 'x', es: 'x' };
const valueDisplay = { kind: 'value' as const, driver: 'v', range: ['lo', 'hi'] as [string, string], tolerance: 3 };
const kpi = (id: string, filter: string, periods: string[], extra: Partial<Kpi>): Kpi =>
  ({ id, aggregator: id, name, description: name, filters: [filter], periods, ...extra }) as Kpi;

const blue = kpi('blue_k', 'sky', ['day'], { visibility: { priority: 1, floor: 0.25, strong: 0.7 } });
const snow = kpi('snow_k', 'snow', ['day', 'morning', 'midday'], {
  display: valueDisplay,
  value: { unit: 'cm' },
  visibility: { priority: 1, floor: 5, strong: 30, slots: { floor: 2, strong: 15 } },
});
const wind = kpi('wind_k', 'access', ['day'], {
  display: valueDisplay,
  value: { unit: 'km/h' },
  visibility: { priority: 0.85, floor: 45, strong: 70, alert: 60 },
});
const chill = kpi('chill_k', 'comfort', ['day'], {
  display: valueDisplay,
  value: { unit: '°C' },
  order: 'asc',
  visibility: { priority: 0.7, floor: -15, strong: -30 },
});
const star = kpi('star_k', 'sky', ['day'], { visibility: { priority: 0.4, floor: 0.5, strong: 0.9 } });
const powder = kpi('powder_k', 'snow', ['day'], { visibility: { priority: 0.9, floor: 0.3, strong: 0.7 } });
const tile = (id: string, k: Kpi): ResolvedTile => ({ tile: { id, format: 'banner', kpis: [k.id] } as Tile, kpis: [k] });
const resolved = [
  tile('snow_t', snow),
  tile('blue_t', blue),
  tile('wind_t', wind),
  tile('chill_t', chill),
  tile('star_t', star),
  tile('powder_t', powder),
];

const config: HomePage = {
  mode: 'scored',
  limit: 50,
  top: 3,
  pinned: [{ tile: 'blue_t', period: 'day' }],
  fallback: [{ tile: 'snow_t', period: 'day' }],
  relevance: {
    slots: { current: 1, next: 0.9, later: 0.7 },
    today: {
      day: [
        { from: '06:00', factor: 1 },
        { from: '12:00', factor: 0.8 },
        { from: '14:00', factor: 0.6 },
      ],
    },
    tomorrow: {
      steps: [
        { from: '17:00', factor: 0.8 },
        { from: '20:00', factor: 1 },
      ],
      slots: { first: 0.9, later: 0.6 },
    },
    early_alerts: { filters: ['access'], from: '12:00', factor: 0.7 },
  },
  reliability: { high: 1, medium: 0.85, low: 0.65, stale: 0.7, coverage_min: 0.5, coverage: 0.8 },
  diversity: { first: 6, per_category: 2 },
};

const D = '2026-12-14';
const T = '2026-12-15';
const at = (day: string, hhmm: string) => `${day}T${hhmm}:00+01:00`;
const GENERATED = '2026-12-14T05:07:00Z';
type Row = [station: string, probability: number, value?: number];
const entry = ([station, probability, value]: Row) => ({
  station_id: station,
  probability,
  confidence: 'high' as const,
  window_start: at(D, '06:00'),
  window_end: at(D, '18:00'),
  members: 50,
  drivers: value === undefined ? {} : { v: value, lo: value, hi: value },
});
const period = (periodId: string, day: string, start: string, end: string, rows: Row[], generated = GENERATED) => ({
  key: `${periodId}@${day}`,
  period_id: periodId,
  ski_day: day,
  start: at(day, start),
  end: end === '00:00' ? at(T, '00:00') : at(day, end),
  generated_at: generated,
  ranking: rows.map(entry),
});
const stations = Object.fromEntries(['a', 'b', 'c', 'd'].map((id) => [id, { id, name: id, short_name: id }]));

interface Values {
  blue?: Row[];
  snowDay?: Row[];
  snowMorning?: Row[];
  windToday?: Row[];
  windTomorrow?: Row[];
  chill?: Row[];
  star?: Row[];
  powder?: Row[];
  snowTomorrow?: Row[];
  staleSnow?: boolean;
}
const payload = (v: Values): MassifDaily =>
  ({
    schema_version: 2,
    massif_id: 'pyrenees',
    forecast_date: D,
    generated_at: GENERATED,
    timezone: 'Europe/Paris',
    stations,
    sources: [],
    kpis: {
      blue_k: { kpi_id: 'blue_k', aggregator_version: '1', periods: [
        period('day', D, '06:00', '18:00', v.blue ?? [['a', 0.12], ['b', 0.1], ['c', 0.05]]),
        period('day', T, '06:00', '18:00', v.blue ?? [['a', 0.12]]),
      ] },
      snow_k: { kpi_id: 'snow_k', aggregator_version: '1', periods: [
        period('day', D, '06:00', '18:00', v.snowDay ?? [], v.staleSnow ? '2026-12-13T23:07:00Z' : GENERATED),
        period('morning', D, '06:00', '12:00', v.snowMorning ?? []),
        period('midday', D, '12:00', '14:00', []),
        period('day', T, '06:00', '18:00', v.snowTomorrow ?? []),
      ] },
      wind_k: { kpi_id: 'wind_k', aggregator_version: '1', periods: [
        period('day', D, '06:00', '18:00', v.windToday ?? []),
        period('day', T, '06:00', '18:00', v.windTomorrow ?? []),
      ] },
      chill_k: { kpi_id: 'chill_k', aggregator_version: '1', periods: [period('day', D, '06:00', '18:00', v.chill ?? [])] },
      star_k: { kpi_id: 'star_k', aggregator_version: '1', periods: [period('day', D, '06:00', '18:00', v.star ?? [])] },
      powder_k: { kpi_id: 'powder_k', aggregator_version: '1', periods: [period('day', D, '06:00', '18:00', v.powder ?? [])] },
    },
  }) as unknown as MassifDaily;

const ids = (feed: ReturnType<typeof homeFeed>) => feed.instances.map((i) => i.id);
const time = (day: string, hhmm: string) => Date.parse(at(day, hhmm));
const feed = (v: Values, now: number, extra: Partial<HomePage> = {}, only: Set<string> | null = null) =>
  ids(homeFeed(resolved, payload(v), now, { config: { ...config, ...extra }, only }));

describe('ski day clock and steps', () => {
  it('counts minutes from 06:00, after midnight included', () => {
    expect(clockOf('06:00')).toBe(0);
    expect(clockOf('17:00')).toBe(660);
    expect(clockOf('01:00')).toBe(1140);
    expect(skiClock(time(D, '10:30'), 'Europe/Paris')).toBe(270);
  });

  it('gives the factor of the last step reached, 0 before the first one', () => {
    const steps = config.relevance!.tomorrow.steps;
    expect(stepFactor(steps, clockOf('16:59'))).toBe(0);
    expect(stepFactor(steps, clockOf('18:00'))).toBe(0.8);
    expect(stepFactor(steps, clockOf('01:00'))).toBe(1);
  });
});

describe('impact and reliability', () => {
  it('rises linearly from the floor to strong, both ways, and is null below the floor', () => {
    expect(impactOf(17.5, 5, 30)).toBeCloseTo(0.5);
    expect(impactOf(50, 5, 30)).toBe(1);
    expect(impactOf(4, 5, 30)).toBeNull();
    expect(impactOf(-22.5, -15, -30)).toBeCloseTo(0.5);
    expect(impactOf(-10, -15, -30)).toBeNull();
  });

  it('averages the confidence and penalises stale values and a poor coverage', () => {
    expect(reliabilityOf(['high', 'medium', 'low'], false, 1)).toBeCloseTo(0.8333, 3);
    expect(reliabilityOf(['high'], true, 1)).toBeCloseTo(0.7);
    expect(reliabilityOf(['high'], false, 0.25)).toBeCloseTo(0.8);
  });
});

describe('homeFeed', () => {
  const morning = time(D, '10:00');

  it('pins the bluebird day first even when it is not significant, then ranks by score', () => {
    const v: Values = {
      snowDay: [['a', 0.9, 50], ['b', 0.9, 50], ['c', 0.9, 50]],
      star: [['a', 0.95], ['b', 0.95], ['c', 0.95]],
      chill: [['a', 0.5, -22.5], ['b', 0.5, -22.5], ['c', 0.5, -22.5]],
    };
    // snow 1 × 1 = 1; chill 0.7 × 0.5 = 0.35; star 0.4 × 1 = 0.4
    expect(feed(v, morning)).toEqual([
      'blue_t--day-2026-12-14',
      'snow_t--day-2026-12-14',
      'star_t--day-2026-12-14',
      'chill_t--day-2026-12-14',
    ]);
  });

  it('hides the tiles below their floor and keeps one tile per KPI, its best period', () => {
    const v: Values = {
      snowDay: [['a', 0.9, 4], ['b', 0.9, 4], ['c', 0.9, 4]],
      snowMorning: [['a', 0.9, 10], ['b', 0.9, 10], ['c', 0.9, 10]],
      star: [['a', 0.3]],
    };
    // the day (4 cm < 5) is hidden; the morning slot (10 cm, slot floor 2) is shown once
    expect(feed(v, morning)).toEqual(['blue_t--day-2026-12-14', 'snow_t--morning-2026-12-14']);
  });

  it('puts alerts right after the pinned tiles', () => {
    const v: Values = {
      snowDay: [['a', 0.9, 50], ['b', 0.9, 50], ['c', 0.9, 50]],
      windToday: [['a', 0.9, 62], ['b', 0.9, 62], ['c', 0.9, 62]],
    };
    expect(feed(v, morning)).toEqual([
      'blue_t--day-2026-12-14',
      'wind_t--day-2026-12-14',
      'snow_t--day-2026-12-14',
    ]);
  });

  it('shows tomorrow from 17:00 only, and an Access alert of tomorrow from noon', () => {
    const v: Values = {
      snowTomorrow: [['a', 0.9, 40], ['b', 0.9, 40], ['c', 0.9, 40]],
      windTomorrow: [['a', 0.9, 65], ['b', 0.9, 65], ['c', 0.9, 65]],
    };
    expect(feed(v, time(D, '11:00'))).toEqual(['blue_t--day-2026-12-14', 'snow_t--day-2026-12-14']);
    expect(feed(v, time(D, '13:00'))).toEqual([
      'blue_t--day-2026-12-14',
      'wind_t--day-2026-12-15',
    ]);
    expect(feed(v, time(D, '17:30'))).toEqual([
      'blue_t--day-2026-12-14',
      'wind_t--day-2026-12-15',
      'snow_t--day-2026-12-15',
    ]);
  });

  it('falls back on the fixed tiles when no tile is significant', () => {
    expect(feed({}, morning)).toEqual(['blue_t--day-2026-12-14', 'snow_t--day-2026-12-14']);
  });

  it('keeps at most `per_category` tiles of a category among the first ones', () => {
    const v: Values = {
      snowDay: [['a', 0.9, 50], ['b', 0.9, 50], ['c', 0.9, 50]],
      powder: [['a', 0.9], ['b', 0.9], ['c', 0.9]],
      star: [['a', 0.95], ['b', 0.95], ['c', 0.95]],
    };
    // powder (0.9) beats star (0.4), but snow already took the only snow place among the first 2
    expect(feed(v, morning, { diversity: { first: 2, per_category: 1 } })).toEqual([
      'blue_t--day-2026-12-14',
      'snow_t--day-2026-12-14',
      'star_t--day-2026-12-14',
      'powder_t--day-2026-12-14',
    ]);
  });

  it('shows at most `limit` tiles, the pinned ones included', () => {
    const v: Values = {
      snowDay: [['a', 0.9, 50], ['b', 0.9, 50], ['c', 0.9, 50]],
      star: [['a', 0.95], ['b', 0.95], ['c', 0.95]],
    };
    expect(feed(v, morning, { limit: 2 })).toEqual(['blue_t--day-2026-12-14', 'snow_t--day-2026-12-14']);
  });

  it('measures the chosen place only', () => {
    const v: Values = {
      snowDay: [['a', 0.9, 50], ['b', 0.9, 50], ['c', 0.9, 50], ['d', 0.1, 1]],
    };
    expect(feed(v, morning, {}, new Set(['d']))).toEqual([
      'blue_t--day-2026-12-14',
      'snow_t--day-2026-12-14', // fallback: 1 cm in that place is not significant
    ]);
    const shown = homeFeed(resolved, payload(v), morning, { config, only: new Set(['a', 'd']) });
    expect(shown.instances.map((i) => i.id)).toContain('snow_t--day-2026-12-14');
  });

  it('ranks stale values lower', () => {
    const v: Values = {
      snowDay: [['a', 0.9, 30], ['b', 0.9, 30], ['c', 0.9, 30]],
      powder: [['a', 0.62], ['b', 0.62], ['c', 0.62]],
    };
    // snow 1.0 vs powder 0.9 × 0.8 = 0.72; stale snow: 0.7
    expect(feed(v, morning)[1]).toBe('snow_t--day-2026-12-14');
    expect(feed({ ...v, staleSnow: true }, morning)[1]).toBe('powder_t--day-2026-12-14');
  });

  it('uses the ranking clock, not the minute clock, for the relevance', () => {
    const v: Values = { snowTomorrow: [['a', 0.9, 40], ['b', 0.9, 40], ['c', 0.9, 40]] };
    const shown = (rankAt: number) =>
      homeFeed(resolved, payload(v), time(D, '17:30'), { config, rankAt }).instances.map((i) => i.id);
    // the page was ranked at 16:00: tomorrow waits for the next re-ranking (period end, new data)
    expect(shown(time(D, '16:00'))).not.toContain('snow_t--day-2026-12-15');
    expect(shown(time(D, '17:30'))).toContain('snow_t--day-2026-12-15');
  });

  it('shows the pinned and fallback tiles as placeholders while the data loads', () => {
    const loading = homeFeed(resolved, null, morning, { config });
    expect(loading.instances).toEqual([]);
    expect(loading.tiles.map((t) => t.tile.id)).toEqual(['blue_t', 'snow_t']);
  });
});
