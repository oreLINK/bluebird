/* Generated from config/schemas/diamond-massif-daily.schema.json by `npm run gen:types`. Do not edit. */

export type SchemaVersion = 1;
export type MassifId = string;
export type ForecastDate = string;
export type GeneratedAt = string;
export type Timezone = string;
export type Id = string;
export type Name = string;
export type Lat = number;
export type Lon = number;
export type Base = number;
export type Mid = number;
export type Summit = number;
export type Aspects = string[];
export type Website = string | null;
export type KpiId = string;
export type AggregatorVersion = string;
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
 * Sorted by probability, descending.
 */
export type Ranking = DiamondRankingEntry[];
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
