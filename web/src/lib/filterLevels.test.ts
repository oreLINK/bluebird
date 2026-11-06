import { describe, expect, it } from 'vitest';
import { type Filter, type Kpi, type ResolvedTile, type Tile, layout } from './config';
import type { MassifDaily } from './data';
import { filterState, nextPath, readFilterPath, writeFilterPath } from './filterLevels';

const name = { fr: 'x', en: 'x', es: 'x' };
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
  tile: { id, format: 'banner', kpis: [k.id] } as Tile,
  kpis: [k],
});
const resolved = [tile('snow_t', snowKpi), tile('white_t', whiteKpi), tile('season_t', seasonKpi)];
/** Fixed home page: the white day pinned, then snow; `gone_t` is not in the layout. */
const home = {
  config: {
    mode: 'fixed' as const,
    pinned: [{ tile: 'white_t', period: 'day' }],
    fallback: [
      { tile: 'gone_t', period: 'day' },
      { tile: 'snow_t', period: 'day' },
    ],
  },
};

const filters: Filter[] = [
  { id: 'rewind', name: { fr: 'Rewind', en: 'Rewind', es: 'Rewind' }, theme: 'rewind' },
  {
    id: 'snow',
    name: { fr: 'Neige', en: 'Snow', es: 'Snow' },
    levels: ['day', 'slot'],
  },
  {
    id: 'sky',
    name: { fr: 'Ciel', en: 'Sky', es: 'Sky' },
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
  it('shows every usable level-1 filter and the fixed home tiles in order', () => {
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

  it('pins the bluebird day first on the repository home page, at most 50 tiles', () => {
    expect(layout.home?.pinned?.[0]).toEqual({ tile: 'bluebird_day', period: 'day' });
    expect(layout.home?.mode).toBe('scored');
    expect(layout.home?.limit).toBe(50);
  });

  it('narrows a topic by day then by time slot, slot tiles only at the slot level', () => {
    const topic = filterState(['snow'], filters, resolved, payload, morning);
    expect(keys(topic)).toEqual(['1:snow*', '2:d0', '2:d1']);
    // Day-grain tiles only: one per day, no morning or evening tile yet.
    expect(ids(topic)).toEqual(['snow_t--day-2026-12-14', 'snow_t--day-2026-12-15']);
    expect(topic.chips[1]?.name.fr).toBe("Aujourd'hui");

    const today = filterState(['snow', 'd0'], filters, resolved, payload, morning);
    expect(keys(today)).toEqual(['1:snow*', '2:d0*', '3:morning', '3:evening']);
    expect(ids(today)).toEqual(['snow_t--day-2026-12-14']);
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

describe('sub-categories', () => {
  const alertKpi = kpi('alert_k', 'snow', ['day']);
  const grouped: Filter[] = [
    {
      id: 'snow',
      name: { fr: 'Neige', en: 'Snow', es: 'Snow' },
      levels: ['group', 'day', 'slot'],
      groups: [
        { id: 'falls', name: { fr: 'Chutes', en: 'Snowfall', es: 'Snowfall' }, kpis: ['snow_k'] },
        { id: 'alerts', name: { fr: 'Alertes', en: 'Alerts', es: 'Alerts' }, kpis: ['alert_k'] },
      ],
    },
    {
      id: 'sky',
      name: { fr: 'Ciel', en: 'Sky', es: 'Sky' },
      levels: ['group', 'day'],
      groups: [{ id: 'white', name: { fr: 'Visibilité', en: 'Visibility', es: 'Visibility' }, kpis: ['white_k'] }],
    },
  ];
  const withAlert = [...resolved, tile('alert_t', alertKpi)];
  const alertPayload = {
    ...payload,
    kpis: {
      ...payload.kpis,
      alert_k: {
        kpi_id: 'alert_k',
        aggregator_version: '1',
        periods: [period('day', D, at(D, '06:00'), at(D, '18:00'))],
      },
    },
  } as MassifDaily;

  it('offers the sub-categories at level 2, then the day and the slot', () => {
    const topic = filterState(['snow'], grouped, withAlert, alertPayload, morning);
    expect(keys(topic)).toEqual(['1:snow*', '2:falls', '2:alerts']);
    // Day-grain tiles of both groups (a tile without data for a day says so).
    expect(ids(topic)).toEqual([
      'snow_t--day-2026-12-14',
      'alert_t--day-2026-12-14',
      'snow_t--day-2026-12-15',
      'alert_t--day-2026-12-15',
    ]);

    const falls = filterState(['snow', 'falls'], grouped, withAlert, alertPayload, morning);
    expect(keys(falls)).toEqual(['1:snow*', '2:falls*', '3:d0', '3:d1']);
    expect(falls.tiles.map((t) => t.tile.id)).toEqual(['snow_t']);

    const slot = filterState(['snow', 'falls', 'd0', 'morning'], grouped, withAlert, alertPayload, morning);
    expect(keys(slot)).toEqual(['1:snow*', '2:falls*', '3:d0*', '4:morning*']);
    expect(ids(slot)).toEqual(['snow_t--morning-2026-12-14']);
  });

  it('skips a level with a single sub-category', () => {
    const sky = filterState(['sky'], grouped, withAlert, alertPayload, morning);
    expect(keys(sky)).toEqual(['1:sky*', '2:d0', '2:d1']);
    const tomorrow = filterState(['sky', 'd1'], grouped, withAlert, alertPayload, morning);
    expect(ids(tomorrow)).toEqual(['white_t--day-2026-12-15']);
    // Removing the day chip goes back to the category.
    expect(nextPath(tomorrow.path, tomorrow.chips[1]!)).toEqual(['sky']);
  });

  it('keeps the sub-category chips while live data loads', () => {
    expect(keys(filterState(['snow'], grouped, withAlert, null, morning))).toEqual([
      '1:snow*',
      '2:falls',
      '2:alerts',
    ]);
  });
});


describe('the Mood filter', () => {
  const moodFilter: Filter = {
    id: 'mood',
    name,
    icon: 'sparkle',
    theme: 'mood',
    levels: ['mood_group', 'mood'],
    moods: [
      {
        id: 'on-site',
        name,
        icon: 'mountain',
        moods: [
          { id: 'snowy', name, kpis: ['snow_k', 'white_k'] },
          { id: 'white', name, kpis: ['white_k'] },
          { id: 'empty', name, kpis: ['gone_k'] },
        ],
      },
      { id: 'on-the-way', name, icon: 'car', tomorrow_only: true, moods: [{ id: 'up', name, kpis: ['snow_k'] }] },
    ],
  };
  const all = [...filters, moodFilter];
  const config = { ...layout.home, mode: 'scored' as const };
  const state = (path: string[]) => filterState(path, all, resolved, payload, morning, { config });

  it('is usable without any KPI tag and keeps its moving theme', () => {
    const home = state([]);
    expect(keys(home)).toEqual(['1:rewind', '1:snow', '1:sky', '1:mood']);
    expect(home.chips.find((c) => c.id === 'mood')?.theme).toBe('mood');
  });

  it('offers the sub-moods, then their moods with a tile, and shows their KPIs', () => {
    const top = state(['mood']);
    expect(keys(top)).toEqual(['1:mood*', '2:on-site', '2:on-the-way']);
    expect(top.chips[1]?.icon).toBe('mountain');
    // every KPI of every mood, one tile each
    expect(top.instances.map((i) => i.kpis[0]?.id).sort()).toEqual(['snow_k', 'white_k']);

    const site = state(['mood', 'on-site']);
    expect(keys(site)).toEqual(['1:mood*', '2:on-site*', '3:snowy', '3:white']);

    const white = state(['mood', 'on-site', 'white']);
    expect(keys(white)).toEqual(['1:mood*', '2:on-site*', '3:white*']);
    expect(white.path).toEqual(['mood', 'on-site', 'white']);
    expect(white.instances.map((i) => i.id)).toEqual(['white_t--day-2026-12-14']);
  });

  it('keeps tomorrow alone under a tomorrow-only sub-mood', () => {
    const up = state(['mood', 'on-the-way', 'up']);
    expect(up.instances.map((i) => i.slot?.skiDay)).toEqual([T]);
  });

  it('drops unknown items of a remembered path', () => {
    expect(state(['mood', 'on-site', 'gone']).path).toEqual(['mood', 'on-site']);
  });
});

describe('remembered filter path', () => {
  it('reads a level-1 id as saved before, and a whole path up to level 4', () => {
    expect(readFilterPath(null)).toEqual([]);
    expect(readFilterPath('snow')).toEqual(['snow']);
    expect(readFilterPath('mood/on-site/freerider')).toEqual(['mood', 'on-site', 'freerider']);
    expect(readFilterPath('a/b/c/d/e')).toEqual(['a', 'b', 'c', 'd']);
    expect(writeFilterPath(['snow', 'falls', 'd0', 'morning'])).toBe('snow/falls/d0/morning');
    expect(writeFilterPath([])).toBe('');
  });
});
