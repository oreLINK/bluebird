import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import type { ServiceStatus } from './data';
import { STATE_ICON, periodLabel, statusView, visiblePeriods, worstState } from './status';

const demo = JSON.parse(
  readFileSync(new URL('../../public/data/diamond/status.json', import.meta.url), 'utf8'),
) as ServiceStatus;

const period = (key: string, end: string, state: ServiceStatus['state']) => ({
  key,
  period_id: key.split('@')[0]!,
  ski_day: key.split('@')[1]!,
  start: '2026-12-14T18:00:00+01:00',
  end,
  state,
  ok: state === 'ok' ? 18 : 12,
  expected: 18,
  updated_at: state === 'stale' ? '2026-12-14T11:07:00Z' : '2026-12-14T17:07:00Z',
});

const status: ServiceStatus = {
  schema_version: 1,
  generated_at: '2026-12-14T17:07:00Z',
  run_id: '20261214T170700Z',
  ski_day: '2026-12-14',
  state: 'down',
  sources: [
    { id: 'a', dataset: null, state: 'ok', ok: null, expected: null },
    { id: 'b', dataset: null, state: 'down', ok: null, expected: null },
  ],
  transforms: [{ id: 'a', dataset: 'x', state: 'partial', ok: 12, expected: 18 }],
  kpis: [
    {
      id: 'snow',
      state: 'stale',
      periods: [
        period('evening@2026-12-14', '2026-12-15T00:00:00+01:00', 'stale'),
        period('night@2026-12-14', '2026-12-15T06:00:00+01:00', 'ok'),
      ],
    },
  ],
  tiles: {
    pyrenees: [
      { tile_id: 'snow_tile', period: period('evening@2026-12-14', '2026-12-15T00:00:00+01:00', 'stale') },
    ],
  },
};

describe('status', () => {
  it('ranks states and gives each one an icon', () => {
    expect(worstState(['ok', 'stale', 'partial'])).toBe('stale');
    expect(worstState([])).toBe('ok');
    expect(Object.keys(STATE_ICON)).toEqual(['ok', 'partial', 'stale', 'down']);
  });

  it('counts degraded items and keeps the details of stale and partial rows', () => {
    const view = statusView(status, 'pyrenees', Date.parse('2026-12-14T18:30:00+01:00'));
    expect(view.state).toBe('down');
    expect(view.degraded).toBe(4); // source b, transform a, KPI snow, the tile
    expect(view.kpis[0]?.issues?.map((p) => p.key)).toEqual(['evening@2026-12-14']);
    expect(view.tiles[0]?.since).toBe('2026-12-14T11:07:00Z');
  });

  it('forgets periods that are over', () => {
    const afterMidnight = Date.parse('2026-12-15T00:30:00+01:00');
    const view = statusView(status, 'pyrenees', afterMidnight);
    expect(view.kpis[0]?.state).toBe('ok');
    expect(view.tiles).toEqual([]);
    expect(visiblePeriods(status.kpis[0]!.periods, afterMidnight)).toHaveLength(1);
  });

  it('names periods like the tiles do', () => {
    const evening = status.kpis[0]!.periods[0]!;
    const label = periodLabel(status, evening, 'Europe/Paris', Date.parse('2026-12-14T18:30:00+01:00'));
    expect(label?.fr).toBe('ce soir');
  });

  it('reads the demo status', () => {
    expect(statusView(demo, 'pyrenees', Date.parse(demo.generated_at)).state).toBe('ok');
  });
});
