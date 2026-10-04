/**
 * One view of a KPI for the tiles, whatever its kind (unit-tested).
 *
 *   live        probabilities of today, from the daily payload
 *               (`diamond/<massif>/latest.json`, fetched at runtime);
 *   historical  values over a closed season, from a Rewind payload
 *               (`config/rewind/<id>/<massif>.json`, bundled at build time).
 *
 * Tiles only read a KpiView: every tile type works for both kinds, and a new
 * kind of data only needs a new builder here. The Rewind of a historical KPI
 * is found from config/rewinds.yaml, so tiles need no Rewind option.
 */
import type { DiamondRewind, Kpi, Rewind } from './config';
import type { MassifDaily, RankingEntry, StationInfo } from './data';
import { formatDriver, formatPercent } from './format';
import type { Locale } from './i18n/core';

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
  /** YYYY-MM-DD the forecast is for (a KPI may look at tomorrow). */
  forecastDate: string;
}

export interface HistoricalView extends ViewBase {
  kind: 'historical';
  rewind: Rewind;
  /** Unit of the values (from the payload, else config/kpis.yaml). */
  unit: string;
}

export type KpiView = LiveView | HistoricalView;

export function liveView(kpi: Kpi, payload: MassifDaily): LiveView {
  const ranking = payload.kpis[kpi.id]?.ranking ?? [];
  return {
    kind: 'live',
    kpi,
    massifId: payload.massif_id,
    ranking,
    forecastDate: payload.forecast_date,
    items: ranking.map((entry) => ({
      stationId: entry.station_id,
      value: entry.probability,
      share: entry.probability,
      confidence: entry.confidence,
      entry,
    })),
    stations: payload.stations,
    timezone: payload.timezone,
    sources: payload.sources,
    generatedAt: payload.generated_at,
  };
}

export function historicalView(
  kpi: Kpi,
  rewind: Rewind,
  massifId: string,
  payload: DiamondRewind | undefined,
): HistoricalView {
  const ranking = payload?.kpis[kpi.id]?.ranking ?? [];
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
 * The value of an item as displayed: "82 %" (live), "4,43 m" / "46 h" /
 * "12 jours", "1 jour" (historical; `value.unit_label` / `unit_label_one` when the
 * unit depends on the language).
 */
export function itemLabel(view: KpiView, item: RankItem, locale: Locale): string {
  if (view.kind === 'live') return formatPercent(item.value, locale);
  const spec = view.kpi.value;
  const singular = new Intl.PluralRules(locale).select(item.value) === 'one';
  const unit =
    (singular ? spec?.unit_label_one?.[locale] : undefined) ?? spec?.unit_label?.[locale] ?? view.unit;
  return formatDriver(item.value, locale, unit, spec?.decimals ?? 0) ?? '';
}

export function shortName(view: KpiView, stationId: string): string {
  const station = view.stations[stationId];
  return station?.short_name ?? station?.name ?? stationId;
}

export function fullName(view: KpiView, stationId: string): string {
  return view.stations[stationId]?.name ?? stationId;
}

/**
 * The view of a tile's KPI: historical KPIs read their Rewind payload (always
 * available, bundled); live KPIs need the daily payload, so `null` means "not
 * loaded yet" (the tile shows its placeholder).
 */
export function viewFor(
  kpi: Kpi | undefined,
  massifId: string,
  live: MassifDaily | null,
  rewinds: Rewind[],
  rewindPayload: (rewindId: string, massifId: string) => DiamondRewind | undefined,
): KpiView | null {
  if (!kpi) return null;
  if (kpi.kind === 'historical') {
    const rewind = rewindOfKpi(kpi.id, rewinds);
    return rewind ? historicalView(kpi, rewind, massifId, rewindPayload(rewind.id, massifId)) : null;
  }
  return live ? liveView(kpi, live) : null;
}
