import { describe, expect, it } from 'vitest';
import type { Kpi, ResolvedTile, Tile } from './config';
import type { MassifDaily } from './data';
import { liveView } from './kpiView';
import {
  addDays,
  daysBetween,
  expandTiles,
  instanceTitle,
  nextBoundary,
  payloadSlots,
  periodsFile,
  referenceDay,
  skiDayAt,
  slotLabel,
} from './periods';

const name = { fr: 'Neige', en: 'Snow' };
const snowKpi: Kpi = {
  id: 'snow',
  aggregator: 'snow',
  name,
  description: name,
  periods: ['day', 'morning', 'midday', 'afternoon', 'evening', 'night'],
};
const powderKpi: Kpi = {
  id: 'powder',
  aggregator: 'powder',
  name: { fr: 'Poudreuse', en: 'Powder' },
  description: name,
  periods: ['morning', 'midday', 'afternoon'],
};
const tile = (id: string, kpi: Kpi, title?: { fr: string; en: string }): ResolvedTile => ({
  tile: { id, type: 'banner', kpis: [kpi.id], ...(title ? { title } : {}) } as Tile,
  kpis: [kpi],
});

/** Paris in winter (UTC+1): local HH:MM on a day → ISO with offset. */
const at = (day: string, hhmm: string) => `${day}T${hhmm}:00+01:00`;

/** A KPI period of ski `day`; hours before 06:00 belong to the next calendar day. */
function period(periodId: string, day: string, start: string, end: string) {
  const calendar = (hhmm: string, isEnd: boolean) =>
    hhmm < '06:00' || (isEnd && hhmm === '06:00' && start < '06:00') || (isEnd && end <= start)
      ? addDays(day, 1)
      : day;
  return {
    key: `${periodId}@${day}`,
    period_id: periodId,
    ski_day: day,
    start: at(calendar(start, false), start),
    end: at(calendar(end, true), end),
    generated_at: '2026-12-14T17:07:00Z',
    ranking: [
      {
        station_id: 'alpha',
        probability: 0.5,
        confidence: 'high' as const,
        window_start: at(day, start),
        window_end: at(day, end),
        members: 91,
        drivers: {},
      },
    ],
  };
}

const D = '2026-12-14';
const T = '2026-12-15';
const payload: MassifDaily = {
  schema_version: 2,
  massif_id: 'pyrenees',
  forecast_date: D,
  generated_at: '2026-12-14T17:07:00Z',
  timezone: 'Europe/Paris',
  stations: {},
  sources: [],
  kpis: {
    snow: {
      kpi_id: 'snow',
      aggregator_version: '2',
      periods: [
        period('evening', D, '18:00', '00:00'),
        period('night', D, '00:00', '06:00'),
        period('day', T, '06:00', '18:00'),
        period('morning', T, '06:00', '12:00'),
      ],
    },
    powder: {
      kpi_id: 'powder',
      aggregator_version: '2',
      periods: [{ ...period('morning', T, '06:00', '12:00'), generated_at: '2026-12-14T11:07:00Z' }],
    },
  },
};

const ms = (iso: string) => Date.parse(iso);

describe('dates', () => {
  it('shifts and compares ISO dates', () => {
    expect(addDays('2026-12-31', 1)).toBe('2027-01-01');
    expect(daysBetween('2026-12-14', '2026-12-15')).toBe(1);
  });

  it('starts the ski day at 06:00 local time', () => {
    expect(skiDayAt(ms('2026-12-14T04:59:00Z'), 'Europe/Paris')).toBe('2026-12-13');
    expect(skiDayAt(ms('2026-12-14T05:00:00Z'), 'Europe/Paris')).toBe('2026-12-14');
    expect(skiDayAt(ms('2026-12-14T23:30:00Z'), 'Europe/Paris')).toBe('2026-12-14');
  });
});

describe('periods', () => {
  it('lists the periods of the payload by start, without those already over', () => {
    const at1830 = ms(at(D, '18:30'));
    expect(payloadSlots(payload, at1830).map((s) => s.key)).toEqual([
      'evening@2026-12-14',
      'night@2026-12-14',
      'day@2026-12-15',
      'morning@2026-12-15',
    ]);
    // At midnight the evening is over; at 06:00 the night is too.
    expect(payloadSlots(payload, ms(at(T, '00:00')))[0]?.key).toBe('night@2026-12-14');
    expect(payloadSlots(payload, ms(at(T, '06:00')))[0]?.key).toBe('day@2026-12-15');
  });

  it('labels periods relative to the ski day, even when a refresh is late', () => {
    const [evening, , , morning] = payloadSlots(payload, ms(at(D, '18:30')));
    const refDay = referenceDay(payload, ms(at(D, '18:30')));
    expect(slotLabel(evening!, refDay)?.fr).toBe('ce soir');
    expect(slotLabel(morning!, refDay)?.fr).toBe('demain matin');
    // 06:30 on the 15th, the 06:00 refresh not published yet: it is "this morning".
    const late = referenceDay(payload, ms(at(T, '06:30')));
    expect(late).toBe(T);
    expect(slotLabel(morning!, late)?.fr).toBe('ce matin');
  });

  it('fills the {period} placeholder, or appends the label to the KPI name', () => {
    const label = { fr: 'ce soir', en: 'this evening' };
    const titled = tile('t', snowKpi, { fr: 'Chute {period}', en: 'Fall {period}' });
    expect(instanceTitle(titled.tile, titled.kpis, label)).toEqual({
      fr: 'Chute ce soir',
      en: 'Fall this evening',
    });
    const plain = tile('t', snowKpi);
    expect(instanceTitle(plain.tile, plain.kpis, label).en).toBe('Snow this evening');
  });

  it('expands each tile into one tile per period, in time then layout order', () => {
    const resolved = [tile('powder_tile', powderKpi), tile('snow_tile', snowKpi)];
    const tiles = expandTiles(resolved, payload, ms(at(D, '18:30')));
    expect(tiles.map((t) => t.id)).toEqual([
      'snow_tile--evening-2026-12-14',
      'snow_tile--night-2026-12-14',
      'snow_tile--day-2026-12-15',
      'powder_tile--morning-2026-12-15',
      'snow_tile--morning-2026-12-15',
    ]);
    const powder = tiles[3]!;
    expect(powder.tile.title?.fr).toBe('Poudreuse demain matin');
    const powderView = liveView(powderKpi, payload, powder.slot);
    expect(powderView.stale).toBe(true); // computed at 12:07, payload at 18:07
    expect(powderView.forecastDate).toBe(T);
    expect(liveView(snowKpi, payload, tiles[0]!.slot).ranking).toHaveLength(1);
    expect(liveView(powderKpi, payload, tiles[0]!.slot).ranking).toEqual([]);
  });

  it('shows Rewind tiles once, after the live ones, even before the forecast loads', () => {
    const seasonKpi: Kpi = { ...snowKpi, id: 'season', kind: 'historical' };
    const resolved = [tile('rewind_tile', seasonKpi), tile('snow_tile', snowKpi)];
    expect(expandTiles(resolved, null, 0).map((t) => [t.id, t.slot])).toEqual([
      ['rewind_tile', null],
    ]);
    const tiles = expandTiles(resolved, payload, ms(at(D, '18:30')));
    expect(tiles.at(-1)?.id).toBe('rewind_tile');
    expect(tiles.at(-1)?.tile.title).toBeUndefined();
  });

  it('wakes the page up when the next period ends', () => {
    expect(nextBoundary(payload, ms(at(D, '18:30')))).toBe(ms(at(T, '00:00')));
    expect(nextBoundary(null, 0)).toBeNull();
  });

  it('bundles periods that cover the ski day with a label for each day', () => {
    for (const p of periodsFile.periods) {
      expect(p.labels.length).toBeGreaterThanOrEqual(periodsFile.horizon_days ?? 2);
    }
  });
});
