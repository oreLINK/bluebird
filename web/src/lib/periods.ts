/**
 * Periods (config/periods.yaml): one tile per configured tile of live KPIs and
 * period, shown until the period is over. Tiles of historical KPIs (Rewinds)
 * are shown once, after them.
 *
 * The payload lists, for each KPI, the periods computed by the last refresh
 * (morning, evening… of today and tomorrow). The page turns every configured
 * tile into one tile per period: the title stays the tile's ("Neige") and the
 * period goes on its time badge (`TileTime`: "Dem. | Matin", "Auj.",
 * "Cette nuit"), coloured by the day and by the moment. A period is hidden as soon as it ends, by the visitor's
 * clock: "ce matin" disappears at 12:00 even if the page stays open.
 *
 * Pure helpers, unit-tested; `now` is always passed in (milliseconds).
 */
import periodsYaml from '@config/periods.yaml';
import type { Kpi, ResolvedTile, Tile } from './config';
import type { MassifDaily } from './data';
import type { BadgeDay, Localized, Period, PeriodsFile } from './generated/periods';
import { localizedFrom, sameInAll } from './i18n/core';

export type { Period };
/** Colour of the moment cell of the time badge (`--tone-<tone>-*` tokens). */
export type TimeTone = NonNullable<Period['tone']>;
/** Colour of the day cell of the time badge (`--when-<tone>` tokens). */
export type DayTone = BadgeDay['tone'];

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

/** Icon of each tone on the time badge (components/Icon.svelte). */
export const TONE_ICONS: Record<TimeTone, string> = {
  morning: 'sunrise',
  midday: 'sun-high',
  afternoon: 'sun-low',
  evening: 'sundown',
  night: 'moon',
};

/** What the time badge of a tile instance shows: "Dem. | Matin", "Auj.", "Cette nuit". */
export interface TileTime {
  /** Day cell: `badge_days` (or `badge_tonight`) of periods.yaml ("Auj.", "Dem."). */
  day: Localized;
  /** Colour of the day cell. */
  when: DayTone;
  /** Moment cell: the period `badge` ("Matin", "PM"); `null` for a whole day or tonight. */
  moment: Localized | null;
  /** Colour of the moment cell; `null` without a moment. */
  tone: TimeTone | null;
  /** Days after the reference day: 0 = today, 1 = tomorrow. */
  offset: number;
  /** The period written out ("demain matin"): screen readers, tile back. */
  label: Localized;
}

/** A configured tile expanded for one period (or shown once, for a Rewind). */
export interface TileInstance {
  /** Unique DOM-safe id, e.g. `snowfall_today--evening-2026-12-14`. */
  id: string;
  /** The configured tile with `id` and `title` resolved (the title has no period). */
  tile: Tile;
  kpis: Kpi[];
  /** The period shown; `null` for a tile of historical KPIs. */
  slot: Slot | null;
  /** Its time badge; `null` for a tile of historical KPIs. */
  time: TileTime | null;
}

/** Whether a tile shows live KPIs (expanded per period) rather than a Rewind. */
export function isLiveTile({ kpis }: Pick<ResolvedTile, 'kpis'>): boolean {
  return (kpis[0]?.kind ?? 'live') === 'live';
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

/**
 * Time badge of a slot, or `undefined` beyond the labels of the horizon:
 * a whole-day period (no `badge`) shows the day alone ("Auj."), today's
 * periods of tone `night` show `badge_tonight` alone ("Cette nuit"), the
 * others the day and the moment ("Dem. | Matin").
 */
export function slotTime(
  slot: Slot,
  refDay: string,
  periods: Period[] = periodsFile.periods,
  file: Pick<PeriodsFile, 'badge_days' | 'badge_tonight'> = periodsFile,
): TileTime | undefined {
  const offset = daysBetween(refDay, slot.skiDay);
  const period = periods.find((p) => p.id === slot.periodId);
  const label = offset < 0 ? undefined : period?.labels[offset];
  if (!period || !label) return undefined;
  if (offset === 0 && period.tone === 'night' && file.badge_tonight) {
    const { tone: when, label: day } = file.badge_tonight;
    return { day, when, moment: null, tone: null, offset, label };
  }
  const badgeDay = file.badge_days?.[offset];
  if (!badgeDay) return undefined;
  const moment = period.badge ?? null;
  const tone = moment ? (period.tone ?? null) : null;
  return { day: badgeDay.label, when: badgeDay.tone, moment, tone, offset, label };
}

/** When a slot happens, for the tile back (`KpiBack`): dates are `YYYY-MM-DD`, times ISO. */
export type SlotDates =
  /** A whole day (no moment): "samedi 16 janvier, toute la journée". */
  | { kind: 'day'; date: string }
  /** A whole night (native window, tone `night`): "nuit du 15 au 16". */
  | { kind: 'night'; date: string; next: string }
  /** Another day-grain period (sunset): its day; hours are in the time window. */
  | { kind: 'date'; date: string }
  /** A time slot: its calendar day and hours ("samedi 16 janvier, 06:00 – 12:00"). */
  | { kind: 'slot'; date: string; start: string; end: string };

/** The dates of a slot in the massif time zone (pure). */
export function slotDates(
  slot: Slot,
  timeZone: string,
  periods: Period[] = periodsFile.periods,
): SlotDates {
  const period = periods.find((p) => p.id === slot.periodId);
  if (period?.native_window) {
    if (!period.badge) return { kind: 'day', date: slot.skiDay };
    if (period.tone === 'night') return { kind: 'night', date: slot.skiDay, next: addDays(slot.skiDay, 1) };
    return { kind: 'date', date: slot.skiDay };
  }
  const date = new Intl.DateTimeFormat('en-CA', { timeZone }).format(new Date(slot.start));
  return { kind: 'slot', date, start: slot.start, end: slot.end };
}

/** One line of the time badge legend (page "Lire une tuile", block `time_badges`). */
export interface TimeLegendItem {
  time: TileTime;
  /** What the badge means: a day chip ("Aujourd'hui") or a slot chip ("Matin"). */
  name: Localized;
  /** Local hours of a time slot ("06:00", "12:00"); absent for a day. */
  hours?: [string, string];
}

/**
 * Every time badge, built from periods.yaml: the days alone (today, tonight,
 * tomorrow), then today's badge for each moment, with its slot hours.
 */
export function timeLegend(file: PeriodsFile = periodsFile): {
  days: TimeLegendItem[];
  moments: TimeLegendItem[];
} {
  const days: TimeLegendItem[] = [];
  const night = file.periods.find((p) => !p.native_window && p.tone === 'night');
  file.badge_days?.forEach((badgeDay, offset) => {
    const name = file.days?.[offset] ?? badgeDay.label;
    const time = { day: badgeDay.label, when: badgeDay.tone, moment: null, tone: null, offset, label: name };
    days.push({ time, name });
    if (offset === 0 && file.badge_tonight && night) {
      const label = night.labels[0];
      const tonight = { day: file.badge_tonight.label, when: file.badge_tonight.tone, moment: null, tone: null, offset, label };
      days.push({ time: tonight, name: localizedFrom((l) => label[l].charAt(0).toUpperCase() + label[l].slice(1)) });
    }
  });
  const today = file.badge_days?.[0];
  const moments: TimeLegendItem[] = [];
  for (const period of file.periods) {
    if (period.native_window || !period.badge || !period.tone || !today) continue;
    moments.push({
      time: { day: today.label, when: today.tone, moment: period.badge, tone: period.tone, offset: 0, label: period.labels[0] },
      name: period.chip ?? period.badge,
      hours: [period.start, period.end],
    });
  }
  return { days, moments };
}

/** Period ids a tile is shown for: its own list, or every period of its KPIs. */
export function tilePeriods(tile: Tile, kpis: Kpi[]): string[] {
  if (tile.periods && tile.periods.length > 0) return tile.periods;
  return [...new Set(kpis.flatMap((kpi) => kpi.periods ?? ['day']))];
}

/** Title shown on a tile: its own, else its first KPI's name (never the period). */
export function tileTitle(tile: Tile, kpis: Kpi[]): Localized {
  return tile.title ?? kpis[0]?.name ?? sameInAll('');
}

/**
 * The title with the period written out ("Neige demain matin"), where no time
 * badge is drawn: accessible names, the service status page.
 */
export function instanceTitle(tile: Tile, kpis: Kpi[], label: Localized): Localized {
  const title = tileTitle(tile, kpis);
  return localizedFrom((l) => `${title[l]} ${label[l]}`.trim());
}

/**
 * One tile per configured tile of live KPIs and period not over at `now`, in
 * time order, then in layout order; then the tiles of historical KPIs, once
 * each, in layout order. A tile whose KPI has no value for a period still
 * appears (it says the data is unavailable) as long as another KPI has it.
 * Without `data` (not loaded yet) only the historical tiles are returned.
 */
export function expandTiles(
  resolved: ResolvedTile[],
  data: MassifDaily | null,
  now: number,
  periods: Period[] = periodsFile.periods,
): TileInstance[] {
  const live = resolved.filter(isLiveTile);
  const instances: TileInstance[] = [];
  if (data) {
    const refDay = referenceDay(data, now);
    for (const slot of payloadSlots(data, now, periods)) {
      const time = slotTime(slot, refDay, periods);
      if (!time) continue;
      for (const { tile, kpis } of live) {
        if (!tilePeriods(tile, kpis).includes(slot.periodId)) continue;
        const id = `${tile.id}--${slot.periodId}-${slot.skiDay}`;
        instances.push({
          id,
          tile: { ...tile, id, title: tileTitle(tile, kpis) },
          kpis,
          slot,
          time,
        });
      }
    }
  }
  for (const { tile, kpis } of resolved.filter((r) => !isLiveTile(r))) {
    instances.push({ id: tile.id, tile, kpis, slot: null, time: null });
  }
  return instances;
}

/** When the next visible period ends (ms), to refresh the page then; `null` if none. */
export function nextBoundary(data: MassifDaily | null, now: number): number | null {
  if (!data) return null;
  const ends = payloadSlots(data, now).map((slot) => Date.parse(slot.end));
  return ends.length > 0 ? Math.min(...ends) : null;
}
