/**
 * Service status (diamond/status.json) as shown in the footer: one row per
 * data source, transformation, KPI and tile of the current massif, each
 * `ok` / `partial` / `stale` / `down`. Periods already over are left out, by the
 * visitor's clock, like the tiles themselves.
 *
 * Pure helpers, unit-tested; `now` is passed in (milliseconds).
 */
import type { ServiceStatus } from './data';
import type { Localized } from './generated/periods';
import { type Slot, skiDayAt, slotLabel } from './periods';

export type StateId = ServiceStatus['state'];
export type StatusPeriod = ServiceStatus['kpis'][number]['periods'][number];

/** Icon of each state: never rely on colour alone. */
export const STATE_ICON: Record<StateId, string> = {
  ok: 'check',
  partial: 'info',
  stale: 'clock',
  down: 'alert',
};

const SEVERITY: Record<StateId, number> = { ok: 0, partial: 1, stale: 2, down: 3 };

export function worstState(states: Iterable<StateId>, fallback: StateId = 'ok'): StateId {
  let worst: StateId | null = null;
  for (const state of states) if (worst === null || SEVERITY[state] > SEVERITY[worst]) worst = state;
  return worst ?? fallback;
}

/** Periods not over at `now`. */
export function visiblePeriods<T extends { end: string }>(periods: readonly T[], now: number): T[] {
  return periods.filter((p) => Date.parse(p.end) > now);
}

export interface StatusRow {
  /** Unique within its group. */
  id: string;
  state: StateId;
  /** Stations with data / expected, when known. */
  ok?: number | null;
  expected?: number | null;
  /** When the values shown were computed (stale rows). */
  since?: string | null;
  /** Visible periods that are not ok (KPI rows only). */
  issues?: StatusPeriod[];
}

export interface StatusView {
  state: StateId;
  /** Rows that are not ok. */
  degraded: number;
  sources: StatusRow[];
  transforms: StatusRow[];
  kpis: StatusRow[];
  tiles: (StatusRow & { tileId: string; period: StatusPeriod })[];
}

/** What the footer shows for `massifId` at `now`. */
export function statusView(status: ServiceStatus, massifId: string, now: number): StatusView {
  const item = (i: ServiceStatus['sources'][number]): StatusRow => ({
    id: i.id,
    state: i.state,
    ok: i.ok,
    expected: i.expected,
  });
  const sources = status.sources.map(item);
  const transforms = status.transforms.map(item);
  const kpis = status.kpis.map((kpi): StatusRow => {
    const periods = visiblePeriods(kpi.periods, now);
    const issues = periods.filter((p) => p.state !== 'ok');
    return {
      id: kpi.id,
      state: worstState(periods.map((p) => p.state), periods.length ? 'ok' : kpi.state),
      issues,
    };
  });
  const tiles = visiblePeriods(
    (status.tiles[massifId] ?? []).map((t) => ({ ...t, end: t.period.end })),
    now,
  ).map((t) => ({
    id: `${t.tile_id}@${t.period.key}`,
    tileId: t.tile_id,
    period: t.period,
    state: t.period.state,
    ok: t.period.ok,
    expected: t.period.expected,
    since: t.period.updated_at,
  }));
  const all = [...sources, ...transforms, ...kpis, ...tiles];
  return {
    state: worstState(all.map((row) => row.state)),
    degraded: all.filter((row) => row.state !== 'ok').length,
    sources,
    transforms,
    kpis,
    tiles,
  };
}

/** Label of a status period ("ce soir"), relative to the status or current ski day. */
export function periodLabel(
  status: ServiceStatus,
  period: StatusPeriod,
  timeZone: string,
  now: number,
): Localized | undefined {
  const current = skiDayAt(now, timeZone);
  const refDay = current > status.ski_day ? current : status.ski_day;
  const slot: Slot = {
    key: period.key,
    periodId: period.period_id,
    skiDay: period.ski_day,
    start: period.start,
    end: period.end,
  };
  return slotLabel(slot, refDay);
}
