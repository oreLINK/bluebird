import { describe, expect, it } from 'vitest';
import { type Filter, type Kpi, type ResolvedTile, type Tile, layout } from './config';
import type { MassifDaily } from './data';
import { filterState, nextPath } from './filterLevels';

const name = { fr: 'x', en: 'x' };
const kpi = (id: string, filter: string, periods?: Kpi['periods'], kind?: 'historical'): Kpi => ({
  id,
  aggregator: id,
  name,
  description: name,
  filters: [filter],
  ...(periods ? { periods } : {}),
  ...(kind ? { kind } : {}),
});
const snowKpi = kpi('snow_k', 'snow', ['day', 'morning', 'evening']);
const whiteKpi = kpi('white_k', 'sky', ['day']);
const seasonKpi = kpi('season_k', 'rewind', undefined, 'historical');
const tile = (id: string, k: Kpi): ResolvedTile => ({
  tile: { id, type: 'banner', kpis: [k.id] } as Tile,
  kpis: [k],
});
const resolved = [tile('snow_t', snowKpi), tile('white_t', whiteKpi), tile('season_t', seasonKpi)];
/** Home page in priority order: the white day first, then snow; `gone_t` is not in the layout. */
const home = [
  { tile: 'white_t', period: 'day' },
  { tile: 'gone_t', period: 'day' },
  { tile: 'snow_t', period: 'day' },
];

const filters: Filter[] = [
  { id: 'rewind', name: { fr: 'Rewind', en: 'Rewind' }, theme: 'rewind' },
  {
    id: 'snow',
    name: { fr: 'Neige', en: 'Snow' },
    levels: ['day', 'slot'],
  },
  {
    id: 'sky',
    name: { fr: 'Ciel', en: 'Sky' },
    levels: ['day'],
  },
  { id: 'unused', name },
];

const D = '2026-12-14';
const T = '2026-12-15';
/** Paris in winter: local time on a calendar day → ISO with offset. */
const at = (day: string, hhmm: string) => `${day}T${hhmm}:00+01:00`;
const period = (periodId: string, skiDay: string, start: string, end: string) => ({
  key: `${periodId}@${skiDay}`,
  period_id: periodId,
  ski_day: skiDay,
  start,
  end,
  generated_at: '2026-12-14T05:07:00Z',
  ranking: [],
});
const payload: MassifDaily = {
  schema_version: 2,
  massif_id: 'pyrenees',
  forecast_date: D,
  generated_at: '2026-12-14T05:07:00Z',
  timezone: 'Europe/Paris',
  stations: {},
  sources: [],
  kpis: {
    snow_k: {
      kpi_id: 'snow_k',
      aggregator_version: '1',
      periods: [
        period('day', D, at(D, '06:00'), at(D, '18:00')),
        period('morning', D, at(D, '06:00'), at(D, '12:00')),
        period('evening', D, at(D, '18:00'), at(T, '00:00')),
        period('day', T, at(T, '06:00'), at(T, '18:00')),
        period('morning', T, at(T, '06:00'), at(T, '12:00')),
      ],
    },
    white_k: {
      kpi_id: 'white_k',
      aggregator_version: '1',
      periods: [period('day', D, at(D, '06:00'), at(D, '18:00')), period('day', T, at(T, '06:00'), at(T, '18:00'))],
    },
  },
};
const morning = Date.parse(at(D, '07:00'));
const keys = (state: ReturnType<typeof filterState>) => state.chips.map((c) => `${c.key}${c.pressed ? '*' : ''}`);
const ids = (state: ReturnType<typeof filterState>) => state.instances.map((i) => i.id);

describe('filterState', () => {
  it('shows every usable level-1 filter and the home tiles in priority order', () => {
    const state = filterState([], filters, resolved, payload, morning, home);
    expect(keys(state)).toEqual(['1:rewind', '1:snow', '1:sky']);
    expect(ids(state)).toEqual(['white_t--day-2026-12-14', 'snow_t--day-2026-12-14']);
    expect(state.tiles.map((t) => t.tile.id)).toEqual(['white_t', 'snow_t']);
    expect(state.rewind).toBeUndefined();
  });

  it("shows tomorrow's home tile once today's period is over", () => {
    const evening = Date.parse(at(D, '19:00'));
    expect(ids(filterState([], filters, resolved, payload, evening, home))).toEqual([
      'white_t--day-2026-12-15',
      'snow_t--day-2026-12-15',
    ]);
  });

  it('puts the bluebird day of today first on the repository home page', () => {
    expect(layout.home?.[0]).toEqual({ tile: 'bluebird_day', period: 'day' });
  });

  it('narrows a topic by day then by time slot, the chosen chips first', () => {
    const topic = filterState(['snow'], filters, resolved, payload, morning);
    expect(keys(topic)).toEqual(['1:snow*', '2:d0', '2:d1']);
    expect(topic.instances).toHaveLength(5);
    expect(topic.chips[1]?.name.fr).toBe("Aujourd'hui");

    const today = filterState(['snow', 'd0'], filters, resolved, payload, morning);
    expect(keys(today)).toEqual(['1:snow*', '2:d0*', '3:morning', '3:evening']);
    expect(ids(today)).toEqual([
      'snow_t--day-2026-12-14',
      'snow_t--morning-2026-12-14',
      'snow_t--evening-2026-12-14',
    ]);
    expect(today.chips[2]?.name.fr).toBe('Matin');

    const slot = filterState(['snow', 'd0', 'evening'], filters, resolved, payload, morning);
    expect(keys(slot)).toEqual(['1:snow*', '2:d0*', '3:evening*']);
    expect(ids(slot)).toEqual(['snow_t--evening-2026-12-14']);
  });

  it('only offers the days and slots that still have tiles', () => {
    const afternoon = Date.parse(at(D, '13:00'));
    const today = filterState(['snow', 'd0'], filters, resolved, payload, afternoon);
    expect(keys(today)).toEqual(['1:snow*', '2:d0*', '3:evening']);
  });

  it('drops stale path items and stops after the configured levels', () => {
    const stale = filterState(['snow', 'd0', 'morning'], filters, resolved, payload, Date.parse(at(D, '13:00')));
    expect(stale.path).toEqual(['snow', 'd0']);
    expect(filterState(['nope', 'd0'], filters, resolved, payload, morning).path).toEqual([]);
    const white = filterState(['sky', 'd1'], filters, resolved, payload, morning);
    expect(keys(white)).toEqual(['1:sky*', '2:d1*']);
    expect(ids(white)).toEqual(['white_t--day-2026-12-15']);
  });

  it('shows the Rewind alone, without levels, even before the forecast loads', () => {
    const state = filterState(['rewind'], filters, resolved, null, morning);
    expect(keys(state)).toEqual(['1:rewind*']);
    expect(ids(state)).toEqual(['season_t']);
  });

  it('keeps the topic while live data loads (no level options yet)', () => {
    const state = filterState(['snow', 'd0'], filters, resolved, null, morning);
    expect(keys(state)).toEqual(['1:snow*']);
    expect(state.tiles.map((t) => t.tile.id)).toEqual(['snow_t']);
  });
});

describe('nextPath', () => {
  const chip = (level: number, id: string, pressed: boolean) => ({ key: '', id, level, name, pressed });

  it('chooses a chip at its level and removes a pressed one with the levels after it', () => {
    expect(nextPath([], chip(1, 'snow', false))).toEqual(['snow']);
    expect(nextPath(['snow'], chip(2, 'd0', false))).toEqual(['snow', 'd0']);
    expect(nextPath(['snow', 'd0', 'morning'], chip(2, 'd0', true))).toEqual(['snow']);
    expect(nextPath(['snow', 'd0'], chip(1, 'snow', true))).toEqual([]);
  });
});
