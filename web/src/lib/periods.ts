/**
 * Periods (config/periods.yaml): one tile per configured tile and period, shown
 * until the period is over.
 *
 * The payload lists, for each KPI, the periods computed by the last refresh
 * (morning, evening… of today and tomorrow). The page turns every configured
 * tile into one tile per period, titled from its template ("Neige {period}" →
 * "Neige ce soir"), and hides a period as soon as it ends, by the visitor's
 * clock: "ce matin" disappears at 12:00 even if the page stays open.
 *
 * Pure helpers, unit-tested; `now` is always passed in (milliseconds).
 */
import periodsYaml from '@config/periods.yaml';
import type { Kpi, ResolvedTile, Tile } from './config';
import type { KpiPeriod, MassifDaily, RankingEntry } from './data';
import type { Localized, Period, PeriodsFile } from './generated/periods';

export type { Period };

export const periodsFile = periodsYaml as PeriodsFile;

/** One period of one ski day present in the payload. */
export interface Slot {
  /** Stable id, e.g. `evening@2026-12-14`. */
  key: string;
  periodId: string;
  skiDay: string;
  start: string;
  end: string;
}

/** A KPI seen through one period: the shape tile components read. */
export interface KpiView {
  kpi_id: string;
  aggregator_version: string;
  ranking: RankingEntry[];
  /** When these values were computed. */
  generated_at: string;
  /** Computed by an earlier refresh than the payload (the KPI failed since). */
  stale: boolean;
}

/** The payload of a massif narrowed to one period. */
export type MassifView = Omit<MassifDaily, 'kpis'> & {
  kpis: Record<string, KpiView>;
  slot: Slot;
};

/** A configured tile expanded for one period. */
export interface TileInstance {
  /** Unique DOM-safe id, e.g. `snowfall_today--evening-2026-12-14`. */
  id: string;
  /** The configured tile with `id` and `title` resolved for the period. */
  tile: Tile;
  kpis: Kpi[];
  slot: Slot;
  view: MassifView;
}

const DAY_MS = 86_400_000;

/** `YYYY-MM-DD` shifted by `days`. */
export function addDays(isoDate: string, days: number): string {
  const [y, m, d] = isoDate.split('-').map(Number);
  return new Date(Date.UTC(y ?? 1970, (m ?? 1) - 1, (d ?? 1) + days)).toISOString().slice(0, 10);
}

/** Whole days from `from` to `to` (both `YYYY-MM-DD`). */
export function daysBetween(from: string, to: string): number {
  return Math.round((Date.parse(`${to}T00:00:00Z`) - Date.parse(`${from}T00:00:00Z`)) / DAY_MS);
}

/** The ski day running at `now` in `timeZone`: the local date, or the day before before `dayStart`. */
export function skiDayAt(
  now: number,
  timeZone: string,
  dayStart: string = periodsFile.day_start ?? '06:00',
): string {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-CA', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23',
    })
      .formatToParts(new Date(now))
      .map((part) => [part.type, part.value]),
  );
  const date = `${parts.year}-${parts.month}-${parts.day}`;
  return `${parts.hour}:${parts.minute}` < dayStart ? addDays(date, -1) : date;
}

/**
 * Ski day the labels are relative to ("ce soir" vs "demain soir"): the
 * payload's, or the visitor's when the payload is older (a refresh is late).
 */
export function referenceDay(data: MassifDaily, now: number): string {
  const current = skiDayAt(now, data.timezone);
  return current > data.forecast_date ? current : data.forecast_date;
}

function periodOrder(periods: Period[]): Map<string, number> {
  return new Map(periods.map((p, index) => [p.id, index]));
}

/** Every period of the payload (any KPI) not over at `now`, by start time. */
export function payloadSlots(
  data: MassifDaily,
  now: number,
  periods: Period[] = periodsFile.periods,
): Slot[] {
  const slots = new Map<string, Slot>();
  for (const kpi of Object.values(data.kpis)) {
    for (const p of kpi.periods) {
      if (Date.parse(p.end) <= now || slots.has(p.key)) continue;
      slots.set(p.key, {
        key: p.key,
        periodId: p.period_id,
        skiDay: p.ski_day,
        start: p.start,
        end: p.end,
      });
    }
  }
  const order = periodOrder(periods);
  return [...slots.values()].sort(
    (a, b) =>
      Date.parse(a.start) - Date.parse(b.start) ||
      (order.get(a.periodId) ?? 99) - (order.get(b.periodId) ?? 99),
  );
}

/** Label of a slot ("ce soir", "demain matin"), or `undefined` beyond the labels. */
export function slotLabel(
  slot: Slot,
  refDay: string,
  periods: Period[] = periodsFile.periods,
): Localized | undefined {
  const offset = daysBetween(refDay, slot.skiDay);
  if (offset < 0) return undefined;
  return periods.find((p) => p.id === slot.periodId)?.labels[offset];
}

/** Period ids a tile is shown for: its own list, or every period of its KPIs. */
export function tilePeriods(tile: Tile, kpis: Kpi[]): string[] {
  if (tile.periods && tile.periods.length > 0) return tile.periods;
  return [...new Set(kpis.flatMap((kpi) => kpi.periods ?? ['day']))];
}

/** Title of a tile for a period: its template with `{period}` filled in. */
export function instanceTitle(tile: Tile, kpis: Kpi[], label: Localized): Localized {
  const name = kpis[0]?.name;
  const template = tile.title ?? {
    fr: `${name?.fr ?? ''} {period}`.trim(),
    en: `${name?.en ?? ''} {period}`.trim(),
  };
  return {
    fr: template.fr.replace('{period}', label.fr),
    en: template.en.replace('{period}', label.en),
  };
}

/** The payload narrowed to one slot: `kpis[id].ranking` is that period's ranking. */
export function massifView(data: MassifDaily, slot: Slot): MassifView {
  const kpis: Record<string, KpiView> = {};
  for (const [id, kpi] of Object.entries(data.kpis)) {
    const period: KpiPeriod | undefined = kpi.periods.find((p) => p.key === slot.key);
    if (!period) continue;
    kpis[id] = {
      kpi_id: kpi.kpi_id,
      aggregator_version: kpi.aggregator_version,
      ranking: period.ranking,
      generated_at: period.generated_at,
      stale: Date.parse(period.generated_at) < Date.parse(data.generated_at),
    };
  }
  return { ...data, kpis, slot };
}

/**
 * One tile per configured tile and period not over at `now`, in time order,
 * then in layout order. A tile whose KPI has no value for a period still
 * appears (it says the data is unavailable) as long as another KPI has it.
 */
export function expandTiles(
  resolved: ResolvedTile[],
  data: MassifDaily,
  now: number,
  periods: Period[] = periodsFile.periods,
): TileInstance[] {
  const slots = payloadSlots(data, now, periods);
  const refDay = referenceDay(data, now);
  const instances: TileInstance[] = [];
  for (const slot of slots) {
    const label = slotLabel(slot, refDay, periods);
    if (!label) continue;
    const view = massifView(data, slot);
    for (const { tile, kpis } of resolved) {
      if (!tilePeriods(tile, kpis).includes(slot.periodId)) continue;
      const id = `${tile.id}--${slot.periodId}-${slot.skiDay}`;
      instances.push({
        id,
        tile: { ...tile, id, title: instanceTitle(tile, kpis, label) },
        kpis,
        slot,
        view,
      });
    }
  }
  return instances;
}

/** When the next visible period ends (ms), to refresh the page then; `null` if none. */
export function nextBoundary(data: MassifDaily | null, now: number): number | null {
  if (!data) return null;
  const ends = payloadSlots(data, now).map((slot) => Date.parse(slot.end));
  return ends.length > 0 ? Math.min(...ends) : null;
}
