/* Generated from config/schemas/diamond-massif-daily.schema.json by `npm run gen:types`. Do not edit. */

export type SchemaVersion = 2;
export type MassifId = string;
/**
 * Ski day of the run (local date, before 06:00: the day before).
 */
export type ForecastDate = string;
export type GeneratedAt = string;
export type Timezone = string;
export type Id = string;
export type Name = string;
/**
 * Compact name for tiles (falls back to `name`).
 */
export type ShortName = string;
export type Lat = number;
export type Lon = number;
export type Base = number;
export type Mid = number;
export type Summit = number;
export type Aspects = string[];
export type Website = string | null;
export type KpiId = string;
export type AggregatorVersion = string;
/**
 * Stable id across runs, e.g. `evening@2026-12-14`.
 */
export type Key = string;
/**
 * Period id from config/periods.yaml.
 */
export type PeriodId = string;
export type SkiDay = string;
/**
 * Local time, with UTC offset.
 */
export type Start = string;
/**
 * Local time, with UTC offset. Hidden afterwards.
 */
export type End = string;
/**
 * When these values were computed; older than the payload = stale.
 */
export type GeneratedAt1 = string;
export type StationId = string;
export type Probability = number;
export type Confidence = 'low' | 'medium' | 'high';
/**
 * Local time, with UTC offset.
 */
export type WindowStart = string;
/**
 * Local time, with UTC offset.
 */
export type WindowEnd = string;
export type Members = number;
/**
 * Best first: by probability, or by the shown value for a KPI with a `value` display (config/kpis.yaml `display`, `order`).
 */
export type Ranking = DiamondRankingEntry[];
/**
 * Periods not over yet, by start time.
 */
export type Periods = DiamondKpiPeriod[];
export type Id1 = string;
export type Name1 = string;
export type Url = string;
export type License = string | null;
export type Sources = DiamondSource[];

/**
 * ``diamond/{massif_id}/latest.json`` and ``diamond/{massif_id}/{date}.json``.
 */
export interface DiamondMassifDaily {
  schema_version?: SchemaVersion;
  massif_id: MassifId;
  forecast_date: ForecastDate;
  generated_at: GeneratedAt;
  timezone: Timezone;
  stations: Stations;
  kpis: Kpis;
  sources: Sources;
}
export interface Stations {
  [k: string]: DiamondStation;
}
export interface DiamondStation {
  id: Id;
  name: Name;
  short_name: ShortName;
  lat: Lat;
  lon: Lon;
  elevation: DiamondElevation;
  aspects: Aspects;
  website: Website;
}
export interface DiamondElevation {
  base: Base;
  mid: Mid;
  summit: Summit;
}
export interface Kpis {
  [k: string]: DiamondKpi;
}
export interface DiamondKpi {
  kpi_id: KpiId;
  aggregator_version: AggregatorVersion;
  periods: Periods;
}
/**
 * The ranking of one KPI for one period of one ski day.
 */
export interface DiamondKpiPeriod {
  key: Key;
  period_id: PeriodId;
  ski_day: SkiDay;
  start: Start;
  end: End;
  generated_at: GeneratedAt1;
  ranking: Ranking;
}
export interface DiamondRankingEntry {
  station_id: StationId;
  probability: Probability;
  confidence: Confidence;
  window_start: WindowStart;
  window_end: WindowEnd;
  members: Members;
  drivers: Drivers;
}
export interface Drivers {
  [k: string]: number | string | null;
}
export interface DiamondSource {
  id: Id1;
  name: Name1;
  url: Url;
  license: License;
}
