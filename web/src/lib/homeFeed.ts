/**
 * The home page (no filter chosen), ranked by a visibility score (unit-tested).
 *
 *   visibility = priority × impact × relevance × reliability
 *
 *   priority     editorial weight of the KPI (`visibility.priority`, kpis.yaml)
 *   impact       how significant the data is: the mean of the top `top`
 *                stations of the chosen place (median value or probability),
 *                (measure − floor) / (strong − floor), clamped to 0..1;
 *                below `floor` the tile is hidden
 *   relevance    the time of day (layout.yaml `home.relevance`): slot in
 *                progress, next or later; steps of today's day-grain periods;
 *                tomorrow only from its first step (17:00), or from noon for
 *                an alert of an `early_alerts` filter (Access)
 *   reliability  confidence of the top stations, × `stale` for values of an
 *                earlier refresh, × `coverage` when few stations have a value
 *
 * Order: pinned tiles (bluebird day) whatever their score, then alerts, then
 * the others by score, one tile per KPI (its best period), at most
 * `per_category` tiles of one category among the first `first`, `limit` tiles
 * in all. With no significant tile: pinned + `fallback`. The score is never
 * shown: it only orders the page. README.md "Home page visibility score".
 *
 * Mood pages (`moodFeed`, the Mood filter of config/filters.yaml) use the same
 * score over the KPIs of the mood, but show all of them (insignificant ones
 * last, by priority), pin nothing and keep no category rule; a
 * `tomorrow_only` sub-mood shows tomorrow alone, at any hour.
 */
import type { Kpi, ResolvedTile } from './config';
import type { MassifDaily } from './data';
import type { KpiVisibility } from './generated/kpis';
import type { HomePage, HomeReliability, HomeTile, RelevanceStep } from './generated/layout';
import { type LiveView, displayOf, liveView } from './kpiView';
import { type Period, type TileInstance, expandTiles, isLiveTile, periodsFile } from './periods';

/** Defaults of the optional fields, the same as the pipeline models (config.py). */
const DEFAULTS = {
  limit: 50,
  top: 3,
  slots: { current: 1, next: 0.9, later: 0.7 },
  tomorrowSlots: { first: 0.9, later: 0.6 },
  reliability: { high: 1, medium: 0.85, low: 0.65, stale: 0.7, coverage_min: 0.5, coverage: 0.8 },
  diversity: { first: 6, per_category: 2 },
} as const;

export interface HomeOptions {
  /** layout.yaml `home`; without it the home page is empty. */
  config?: HomePage;
  /** Stations of the chosen place (lib/geoLevels.ts); `null` = the whole massif. */
  only?: Set<string> | null;
  /** Clock of the ranking, kept between period ends so the page does not reshuffle. */
  rankAt?: number;
}

/** The parts of a candidate's score (tests; never shown on the site). */
export interface Visibility {
  /** Mean of the top stations; `NaN` without any value. */
  measure: number;
  /** The measure reaches the floor (impact counts); otherwise impact is 0. */
  significant: boolean;
  impact: number;
  relevance: number;
  reliability: number;
  alert: boolean;
  score: number;
}

const toMinutes = (hhmm: string): number => {
  const [h, m] = hhmm.split(':').map(Number);
  return (h ?? 0) * 60 + (m ?? 0);
};

/** Minutes after `dayStart` of a local time "HH:MM" (0..1439): the ski day clock. */
export function clockOf(hhmm: string, dayStart: string = periodsFile.day_start ?? '06:00'): number {
  return (((toMinutes(hhmm) - toMinutes(dayStart)) % 1440) + 1440) % 1440;
}

/** The ski day clock at `now` in `timeZone`. */
export function skiClock(now: number, timeZone: string, dayStart?: string): number {
  const hhmm = new Intl.DateTimeFormat('en-GB', {
    timeZone,
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).format(new Date(now));
  return clockOf(hhmm, dayStart);
}

/** Factor of the last step reached at `clock`, 0 before the first one. */
export function stepFactor(steps: RelevanceStep[], clock: number, dayStart?: string): number {
  let factor = 0;
  for (const step of steps) if (clockOf(step.from, dayStart) <= clock) factor = step.factor;
  return factor;
}

/** Floor and strong of a KPI for a period: the `slots` ones for a time slot. */
function thresholds(vis: KpiVisibility, period: Period | undefined): { floor: number; strong: number } {
  return !period?.native_window && vis.slots ? vis.slots : vis;
}

/** What the thresholds compare: the display value or the probability. */
export function measureKind(kpi: Kpi): 'value' | 'probability' {
  return kpi.visibility?.measure ?? (displayOf(kpi).kind === 'value' ? 'value' : 'probability');
}

/**
 * Impact of a measure: (measure − floor) / (strong − floor), clamped to 0..1
 * (both directions: `strong` below `floor` means lower is stronger);
 * `null` when the measure does not reach the floor (not significant).
 */
export function impactOf(measure: number, floor: number, strong: number): number | null {
  const t = (measure - floor) / (strong - floor);
  return t < 0 ? null : Math.min(1, t);
}

/** Whether a measure reaches the KPI's alert threshold. */
export function isAlert(vis: KpiVisibility, measure: number): boolean {
  if (vis.alert === undefined || vis.alert === null) return false;
  return vis.strong < vis.floor ? measure <= vis.alert : measure >= vis.alert;
}

interface Scored {
  instance: TileInstance;
  index: number;
  kpi: Kpi;
  category: string;
  visibility: Visibility;
}

interface Context {
  config: HomePage;
  periods: Period[];
  dayStart: string;
  rankAt: number;
  clock: number;
  stationCount: number;
}

/** The top stations of a view for the measure: measures and confidences, best first. */
function topOf(kpi: Kpi, view: LiveView, top: number, lowerIsStronger: boolean) {
  const kind = measureKind(kpi);
  const rows = view.items
    .map((item) => ({
      measure: kind === 'value' ? item.value : (item.entry?.probability ?? item.value),
      confidence: item.confidence,
    }))
    .filter((row) => Number.isFinite(row.measure));
  rows.sort((a, b) => (lowerIsStronger ? a.measure - b.measure : b.measure - a.measure));
  return { rows: rows.slice(0, top), known: rows.length };
}

/** Relevance of an instance at the ranking clock (layout.yaml `home.relevance`). */
export function relevanceOf(
  instance: TileInstance,
  kpi: Kpi,
  alert: boolean,
  ctx: Pick<Context, 'config' | 'periods' | 'dayStart' | 'rankAt' | 'clock'>,
  tomorrowOnly = false,
): number {
  const relevance = ctx.config.relevance;
  const { slot, time } = instance;
  if (!relevance || !slot || !time) return 0;
  const period = ctx.periods.find((p) => p.id === slot.periodId);
  if (!period) return 0;
  const span = (p: Period) => {
    const start = clockOf(p.start, ctx.dayStart);
    return { start, end: clockOf(p.end, ctx.dayStart) || 1440 };
  };
  if (time.offset === 0) {
    if (period.native_window) {
      const steps = relevance.today[period.id];
      return steps ? stepFactor(steps, ctx.clock, ctx.dayStart) : 1;
    }
    const slots = { ...DEFAULTS.slots, ...relevance.slots };
    if (Date.parse(slot.start) <= ctx.rankAt && ctx.rankAt < Date.parse(slot.end)) return slots.current;
    const current = ctx.periods.find((p) => {
      if (p.native_window) return false;
      const s = span(p);
      return s.start <= ctx.clock && ctx.clock < s.end;
    });
    return current && span(period).start === span(current).end ? slots.next : slots.later;
  }
  if (time.offset !== 1) return 0;
  const tomorrowSlots = { ...DEFAULTS.tomorrowSlots, ...relevance.tomorrow.slots };
  const periodFactor = period.native_window
    ? 1
    : span(period).start === 0
      ? tomorrowSlots.first
      : tomorrowSlots.later;
  // A page of tomorrow only (mood En route): tomorrow is asked for, at any hour.
  if (tomorrowOnly) return periodFactor;
  const step = stepFactor(relevance.tomorrow.steps, ctx.clock, ctx.dayStart);
  if (step > 0) return step * periodFactor;
  const early = relevance.early_alerts;
  const earlyFilter = early?.filters.some((f) => kpi.filters?.includes(f)) ?? false;
  if (early && alert && earlyFilter && clockOf(early.from, ctx.dayStart) <= ctx.clock) {
    return early.factor * periodFactor;
  }
  return 0;
}

/** Reliability of the top stations: mean confidence, stale values, station coverage. */
export function reliabilityOf(
  confidences: (LiveView['items'][number]['confidence'])[],
  stale: boolean,
  coverage: number,
  config: HomeReliability = {},
): number {
  const cfg = { ...DEFAULTS.reliability, ...config };
  const factors = confidences.map((c) => (c === 'high' ? cfg.high : c === 'medium' ? cfg.medium : cfg.low));
  const mean = factors.length ? factors.reduce((a, b) => a + b, 0) / factors.length : 0;
  return mean * (stale ? cfg.stale : 1) * (coverage < cfg.coverage_min ? cfg.coverage : 1);
}

/**
 * The visibility of one live tile instance. `null` only without a KPI
 * `visibility` block or a period; a measure below the floor gives
 * `significant: false` and a score of 0 (the home page hides it, a mood shows
 * it last).
 */
export function visibilityOf(
  instance: TileInstance,
  payload: MassifDaily,
  ctx: Context,
  only: Set<string> | null = null,
  tomorrowOnly = false,
): Visibility | null {
  const kpi = instance.kpis[0];
  const vis = kpi?.visibility;
  if (!kpi || !vis || !instance.slot) return null;
  const period = ctx.periods.find((p) => p.id === instance.slot?.periodId);
  const { floor, strong } = thresholds(vis, period);
  const view = liveView(kpi, payload, instance.slot, only);
  const { rows, known } = topOf(kpi, view, ctx.config.top ?? DEFAULTS.top, strong < floor);
  const measure = rows.length ? rows.reduce((sum, row) => sum + row.measure, 0) / rows.length : Number.NaN;
  const reached = Number.isFinite(measure) ? impactOf(measure, floor, strong) : null;
  const alert = reached !== null && isAlert(vis, measure);
  const relevance = relevanceOf(instance, kpi, alert, ctx, tomorrowOnly);
  const coverage = ctx.stationCount > 0 ? known / ctx.stationCount : 0;
  const reliability = rows.length
    ? reliabilityOf(
        rows.map((row) => row.confidence),
        view.stale,
        coverage,
        ctx.config.reliability,
      )
    : 0;
  const impact = reached ?? 0;
  const score = vis.priority * impact * relevance * reliability;
  return { measure, significant: reached !== null, impact, relevance, reliability, alert, score };
}

/** The first instance of each entry (today's period, or tomorrow's once today's is over). */
function entryInstances(entries: HomeTile[], instances: TileInstance[]): TileInstance[] {
  return entries.flatMap((entry) => {
    const found = instances.find(
      (i) => i.id.startsWith(`${entry.tile}--`) && i.slot?.periodId === entry.period,
    );
    return found ? [found] : [];
  });
}

/** Alerts first, then by score; the first `first` keep at most `per_category` per category. */
function order(scored: Scored[], config: HomePage): Scored[] {
  const { first, per_category } = { ...DEFAULTS.diversity, ...config.diversity };
  const byScore = (a: Scored, b: Scored) =>
    b.visibility.score - a.visibility.score || a.index - b.index;
  const alerts = scored.filter((s) => s.visibility.alert).sort(byScore);
  const rest = scored.filter((s) => !s.visibility.alert).sort(byScore);
  const result = [...alerts];
  const count = new Map<string, number>();
  for (const s of alerts) count.set(s.category, (count.get(s.category) ?? 0) + 1);
  while (result.length < first && rest.length > 0) {
    const index = rest.findIndex((s) => (count.get(s.category) ?? 0) < per_category);
    const [picked] = rest.splice(index === -1 ? 0 : index, 1);
    if (!picked) break;
    result.push(picked);
    count.set(picked.category, (count.get(picked.category) ?? 0) + 1);
  }
  return [...result, ...rest];
}

function contextOf(
  config: HomePage,
  payload: MassifDaily,
  now: number,
  options: HomeOptions,
  periods: Period[],
  dayStart: string,
): Context {
  const rankAt = options.rankAt ?? now;
  return {
    config,
    periods,
    dayStart,
    rankAt,
    clock: skiClock(rankAt, payload.timezone, dayStart),
    stationCount: options.only?.size ?? Object.keys(payload.stations).length,
  };
}

/** Tiles and tile instances of the home page. */
export function homeFeed(
  resolved: ResolvedTile[],
  payload: MassifDaily | null,
  now: number,
  options: HomeOptions = {},
  periods: Period[] = periodsFile.periods,
  dayStart: string = periodsFile.day_start ?? '06:00',
): { tiles: ResolvedTile[]; instances: TileInstance[] } {
  const config = options.config;
  if (!config) return { tiles: [], instances: [] };
  const limit = config.limit ?? DEFAULTS.limit;
  const fixed = [...(config.pinned ?? []), ...(config.fallback ?? [])];
  const tilesOf = (entries: HomeTile[]) => {
    const ids = [...new Set(entries.map((e) => e.tile))];
    return ids.flatMap((id) => resolved.filter((r) => r.tile.id === id));
  };
  if (!payload) return { tiles: tilesOf(fixed), instances: [] };

  const all = expandTiles(resolved, payload, now, periods).filter((i) => i.slot);
  const pinned = entryInstances(config.pinned ?? [], all);
  const pinnedKpis = new Set(pinned.map((i) => i.kpis[0]?.id));
  const finish = (instances: TileInstance[]) => {
    const unique = instances.filter((i, n) => instances.findIndex((j) => j.id === i.id) === n);
    const kept = unique.slice(0, limit);
    const tiles = [...new Set(kept.map((i) => i.tile.id.split('--')[0]))].flatMap((id) =>
      resolved.filter((r) => r.tile.id === id),
    );
    return { tiles, instances: kept };
  };
  if (config.mode === 'fixed' || !config.relevance) {
    return finish([...pinned, ...entryInstances(config.fallback ?? [], all)]);
  }

  const ctx = contextOf(config, payload, now, options, periods, dayStart);
  const best = new Map<string, Scored>();
  all.forEach((instance, index) => {
    const kpi = instance.kpis[0];
    if (!kpi || pinnedKpis.has(kpi.id)) return;
    const visibility = visibilityOf(instance, payload, ctx, options.only ?? null);
    if (!visibility?.significant || visibility.relevance <= 0) return;
    const candidate = { instance, index, kpi, category: kpi.filters?.[0] ?? kpi.id, visibility };
    const current = best.get(kpi.id);
    const better =
      !current ||
      Number(visibility.alert) - Number(current.visibility.alert) > 0 ||
      (visibility.alert === current.visibility.alert && visibility.score > current.visibility.score);
    if (better) best.set(kpi.id, candidate);
  });
  if (best.size === 0) return finish([...pinned, ...entryInstances(config.fallback ?? [], all)]);
  return finish([...pinned, ...order([...best.values()], config).map((s) => s.instance)]);
}

const moodRank = (v: Visibility): number[] => [Number(v.alert && v.relevance > 0), v.score, v.relevance];

/** Lexicographic comparison of two ranks: > 0 when `a` comes first. */
function compareRanks(a: number[], b: number[]): number {
  for (let i = 0; i < a.length; i += 1) {
    const diff = (a[i] ?? 0) - (b[i] ?? 0);
    if (diff !== 0) return diff;
  }
  return 0;
}

export interface MoodOptions extends HomeOptions {
  /** The KPIs of the chosen mood(s) (config/filters.yaml `moods`). */
  kpis: string[];
  /** Tomorrow's periods only, at any hour (sub-mood `tomorrow_only`, e.g. En route). */
  tomorrowOnly?: boolean;
}

/**
 * A mood page: ALL the tiles of its KPIs, one per KPI (its best period, by
 * score, then relevance, then time), ordered like the home page but without
 * pinned tiles nor the category rule and without hiding anything: alerts
 * first, then the significant tiles by score, then the others (score 0) by
 * KPI priority. The time of day still counts (relevance), and tomorrow-only
 * pages keep tomorrow's periods alone.
 */
export function moodFeed(
  resolved: ResolvedTile[],
  payload: MassifDaily | null,
  now: number,
  options: MoodOptions,
  periods: Period[] = periodsFile.periods,
  dayStart: string = periodsFile.day_start ?? '06:00',
): { tiles: ResolvedTile[]; instances: TileInstance[] } {
  const wanted = new Set(options.kpis);
  const tiles = resolved.filter((r) => isLiveTile(r) && wanted.has(r.kpis[0]?.id ?? ''));
  const config = options.config;
  if (!payload || !config) return { tiles, instances: [] };
  const tomorrowOnly = options.tomorrowOnly ?? false;
  const ctx = contextOf(config, payload, now, options, periods, dayStart);
  const best = new Map<string, Scored>();
  expandTiles(tiles, payload, now, periods).forEach((instance, index) => {
    const kpi = instance.kpis[0];
    if (!kpi || !instance.slot || (tomorrowOnly && instance.time?.offset !== 1)) return;
    const visibility = visibilityOf(instance, payload, ctx, options.only ?? null, tomorrowOnly) ?? {
      measure: Number.NaN,
      significant: false,
      impact: 0,
      relevance: 0,
      reliability: 0,
      alert: false,
      score: 0,
    };
    const candidate = { instance, index, kpi, category: kpi.filters?.[0] ?? kpi.id, visibility };
    const current = best.get(kpi.id);
    // Best period: an alert, then the score, then the relevance; the earliest on a tie.
    const better = !current || compareRanks(moodRank(visibility), moodRank(current.visibility)) > 0;
    if (better) best.set(kpi.id, candidate);
  });
  const all = [...best.values()];
  const shown = (s: Scored) => s.visibility.score > 0;
  const byScore = (a: Scored, b: Scored) => b.visibility.score - a.visibility.score || a.index - b.index;
  const priority = (s: Scored) => s.kpi.visibility?.priority ?? 0;
  const alerts = all.filter((s) => s.visibility.alert && shown(s)).sort(byScore);
  const significant = all.filter((s) => !s.visibility.alert && shown(s)).sort(byScore);
  const rest = all
    .filter((s) => !shown(s))
    .sort((a, b) => priority(b) - priority(a) || b.visibility.relevance - a.visibility.relevance || a.index - b.index);
  return { tiles, instances: [...alerts, ...significant, ...rest].map((s) => s.instance) };
}
