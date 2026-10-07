/**
 * One view of a KPI for the tiles, whatever its kind (unit-tested).
 *
 *   live        probabilities for one period (this evening, tomorrow morning…),
 *               from the refreshed payload (`diamond/<massif>/latest.json`,
 *               fetched at runtime);
 *   historical  values over a closed season, from a Rewind payload
 *               (`config/rewind/<id>/<massif>.json`, bundled at build time).
 *
 * Tiles only read a KpiView: every tile type works for both kinds, and a new
 * kind of data only needs a new builder here. The Rewind of a historical KPI
 * is found from config/rewinds.yaml, so tiles need no Rewind option.
 *
 * A live KPI is shown as its `display` says (config/kpis.yaml): `percent`
 * (the probability, optionally with a `note` driver such as the sunset time),
 * `value` (the median of the scenarios, from a driver, with an optional band
 * label such as the wind chill risk) or `levels` (Oui / Possible / Non from
 * the probability). The ranking order comes from the pipeline.
 */
import { type DiamondRewind, type Kpi, type Rewind, stationCountries } from './config';
import { HOME_COUNTRY, flagOf } from './geoLevels';
import type { MassifDaily, RankingEntry, StationInfo } from './data';
import type { Slot } from './periods';
import { formatDriver, formatPercent } from './format';
import { type Locale, pickLocalized } from './i18n/core';
import type { KpiDisplay, Localized } from './generated/kpis';

export type Confidence = RankingEntry['confidence'];

export interface ViewSource {
  id: string;
  name: string;
  url: string;
  license?: string | null;
}

/** One ranked station. */
export interface RankItem {
  stationId: string;
  /** Probability (0..1) for live KPIs; value in the KPI unit for historical ones. */
  value: number;
  /**
   * Length of the bar, 0..1: the probability; for historical KPIs the value
   * over `value.max` (config/kpis.yaml, e.g. 100 for a percentage), or over
   * the highest value of the ranking when no maximum is set (also when the
   * ranking is ascending, e.g. fewest white days first).
   */
  share: number;
  /** Live only: how much the ensemble scenarios agree. */
  confidence?: Confidence;
  /** Live only: the full entry, for the station details. */
  entry?: RankingEntry;
  /** Small text next to the value: a band label ("risque modéré") or a note driver ("17:41"). */
  note?: Localized | string;
}

interface ViewBase {
  kpi: Kpi;
  massifId: string;
  items: RankItem[];
  stations: Record<string, StationInfo>;
  timezone: string;
  sources: ViewSource[];
  /** ISO datetime the data was computed; empty when there is no data yet. */
  generatedAt: string;
}

export interface LiveView extends ViewBase {
  kind: 'live';
  ranking: RankingEntry[];
  /** YYYY-MM-DD: ski day of the period shown. */
  forecastDate: string;
  /** The period shown; `null` reads no period (no ranking). */
  slot: Slot | null;
  /** The values were computed by an earlier refresh than the payload (the KPI failed since). */
  stale: boolean;
}

export interface HistoricalView extends ViewBase {
  kind: 'historical';
  rewind: Rewind;
  /** Unit of the values (from the payload, else config/kpis.yaml). */
  unit: string;
}

export type KpiView = LiveView | HistoricalView;

/** The display of a KPI, `percent` when not configured. */
export function displayOf(kpi: Kpi): KpiDisplay & { kind: 'percent' | 'value' | 'levels' } {
  return { ...kpi.display, kind: kpi.display?.kind ?? 'percent' };
}

/** Label of the band a value falls in (bands sorted by `max`, the last without). */
export function bandOf(display: KpiDisplay, value: number): Localized | undefined {
  return display.bands?.find((band) => band.max === undefined || band.max === null || value <= band.max)
    ?.label;
}

/** Label of the level of a probability (levels sorted by decreasing `min`). */
export function levelOf(display: KpiDisplay, probability: number): Localized | undefined {
  return display.levels?.find((level) => probability >= level.min)?.label;
}

const round = (value: number, decimals: number) => Number(value.toFixed(decimals));

function liveItems(kpi: Kpi, ranking: RankingEntry[]): RankItem[] {
  const display = displayOf(kpi);
  if (display.kind === 'value' && display.driver) {
    const driver = display.driver;
    const decimals = kpi.value?.decimals ?? 0;
    const raw = (entry: RankingEntry) => entry.drivers[driver];
    const values = ranking.map(raw).filter((v): v is number => typeof v === 'number');
    const extreme = kpi.order === 'asc' ? Math.min(0, ...values) : Math.max(0, ...values);
    const full = kpi.value?.max ?? extreme;
    return ranking.map((entry) => {
      const value = raw(entry);
      const known = typeof value === 'number';
      return {
        stationId: entry.station_id,
        value: known ? value : Number.NaN,
        share: known && full !== 0 ? Math.max(0, Math.min(1, value / full)) : 0,
        confidence: entry.confidence,
        entry,
        note: known ? bandOf(display, round(value, decimals)) : undefined,
      };
    });
  }
  return ranking.map((entry) => {
    const note = display.note ? entry.drivers[display.note] : undefined;
    return {
      stationId: entry.station_id,
      value: entry.probability,
      share: entry.probability,
      confidence: entry.confidence,
      entry,
      note: typeof note === 'string' || typeof note === 'number' ? String(note) : undefined,
    };
  });
}

/** Keeps the entries of the chosen place (lib/geoLevels.ts); `null` keeps them all. */
const within = <T extends { station_id: string }>(entries: T[], only: Set<string> | null): T[] =>
  only ? entries.filter((e) => only.has(e.station_id)) : entries;

export function liveView(
  kpi: Kpi,
  payload: MassifDaily,
  slot: Slot | null = null,
  only: Set<string> | null = null,
): LiveView {
  const period = slot ? payload.kpis[kpi.id]?.periods.find((p) => p.key === slot.key) : undefined;
  const ranking = within(period?.ranking ?? [], only);
  return {
    kind: 'live',
    kpi,
    massifId: payload.massif_id,
    ranking,
    forecastDate: slot?.skiDay ?? payload.forecast_date,
    slot,
    stale: period ? Date.parse(period.generated_at) < Date.parse(payload.generated_at) : false,
    items: liveItems(kpi, ranking),
    stations: payload.stations,
    timezone: payload.timezone,
    sources: payload.sources,
    generatedAt: period?.generated_at ?? payload.generated_at,
  };
}

export function historicalView(
  kpi: Kpi,
  rewind: Rewind,
  massifId: string,
  payload: DiamondRewind | undefined,
  only: Set<string> | null = null,
): HistoricalView {
  const ranking = within(payload?.kpis[kpi.id]?.ranking ?? [], only);
  const full = kpi.value?.max ?? Math.max(0, ...ranking.map((e) => e.value));
  return {
    kind: 'historical',
    kpi,
    rewind,
    massifId,
    unit: payload?.kpis[kpi.id]?.unit ?? kpi.value?.unit ?? '',
    items: ranking.map((entry) => ({
      stationId: entry.station_id,
      value: entry.value,
      share: full > 0 ? Math.max(0, Math.min(1, entry.value / full)) : 0,
    })),
    stations: payload?.stations ?? {},
    timezone: payload?.timezone ?? 'UTC',
    sources: payload?.sources ?? [],
    generatedAt: payload?.generated_at ?? '',
  };
}

/** The Rewind a historical KPI belongs to (config/rewinds.yaml `kpis`). */
export function rewindOfKpi(kpiId: string, rewinds: Rewind[]): Rewind | undefined {
  return rewinds.find((r) => r.kpis.includes(kpiId));
}

/**
 * The value of an item as displayed: "82 %", "4 cm", "−24 °C", "Oui" (live,
 * after its `display`), "4,43 m" / "46 h" / "12 jours", "1 jour" (historical;
 * `value.unit_label` / `unit_label_one` when the unit depends on the language).
 */
export function itemLabel(view: KpiView, item: RankItem, locale: Locale): string {
  if (view.kind === 'live') {
    const display = displayOf(view.kpi);
    if (display.kind === 'levels') {
      return pickLocalized(levelOf(display, item.value), locale) || formatPercent(item.value, locale);
    }
    if (display.kind === 'percent') return formatPercent(item.value, locale);
    if (!Number.isFinite(item.value)) return '—';
  }
  const spec = view.kpi.value;
  const singular = new Intl.PluralRules(locale).select(item.value) === 'one';
  const unit =
    (singular ? spec?.unit_label_one?.[locale] : undefined) ??
    spec?.unit_label?.[locale] ??
    (view.kind === 'historical' ? view.unit : spec?.unit);
  return formatDriver(item.value, locale, unit, spec?.decimals ?? 0) ?? '';
}

/** The small text next to an item's value ("risque modéré", "17:41"), or "". */
export function itemNote(item: RankItem, locale: Locale): string {
  if (item.note === undefined) return '';
  return typeof item.note === 'string' ? item.note : pickLocalized(item.note, locale);
}

/** Whether a view shows probabilities (and so can show decimal odds). */
export function showsPercent(view: KpiView): boolean {
  return view.kind === 'live' && displayOf(view.kpi).kind === 'percent';
}

/**
 * Name shown in the tiles: the short name, with its country's flag for a
 * resort abroad (🇪🇸 Baqueira). `countries` maps station ids to ISO codes.
 */
export function shortName(
  view: KpiView,
  stationId: string,
  countries: Map<string, string> = stationCountries,
): string {
  const station = view.stations[stationId];
  const name = station?.short_name ?? station?.name ?? stationId;
  const country = countries.get(stationId) ?? HOME_COUNTRY;
  return country === HOME_COUNTRY ? name : `${flagOf(country)} ${name}`;
}

/** Full official name, without flag (accessible labels, station details). */
export function fullName(view: KpiView, stationId: string): string {
  return view.stations[stationId]?.name ?? stationId;
}

/**
 * The view of a tile's KPI: historical KPIs read their Rewind payload (always
 * available, bundled); live KPIs need the refreshed payload and the period of
 * the tile, so `null` means "not loaded yet" (the tile shows its placeholder).
 * `only` restricts the ranking to the chosen place (département, linked area):
 * ranks, bars and the reliability index then describe those stations only.
 */
export function viewFor(
  kpi: Kpi | undefined,
  massifId: string,
  live: MassifDaily | null,
  rewinds: Rewind[],
  rewindPayload: (rewindId: string, massifId: string) => DiamondRewind | undefined,
  slot: Slot | null = null,
  only: Set<string> | null = null,
): KpiView | null {
  if (!kpi) return null;
  if (kpi.kind === 'historical') {
    const rewind = rewindOfKpi(kpi.id, rewinds);
    const payload = rewind ? rewindPayload(rewind.id, massifId) : undefined;
    return rewind ? historicalView(kpi, rewind, massifId, payload, only) : null;
  }
  return live ? liveView(kpi, live, slot, only) : null;
}
