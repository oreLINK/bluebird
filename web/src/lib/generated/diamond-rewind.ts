/* Generated from config/schemas/diamond-rewind.schema.json by `npm run gen:types`. Do not edit. */

export type SchemaVersion = 1;
export type RewindId = string;
export type MassifId = string;
/**
 * First day of the season (local), included.
 */
export type Start = string;
/**
 * Last day of the season (local), included.
 */
export type End = string;
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
export type Unit = string;
export type StationId = string;
export type Value = number;
/**
 * Best first: by value, descending unless the KPI `order` is asc.
 */
export type Ranking = DiamondRewindEntry[];
export type Id1 = string;
export type Name1 = string;
export type Url = string;
export type License = string | null;
export type Sources = DiamondSource[];

/**
 * ``config/rewind/{rewind_id}/{massif_id}.json``: a closed season, ranked.
 *
 * Generated once by ``bluebird rewind`` and committed (the site bundles it at
 * build time); never edited by hand.
 */
export interface DiamondRewind {
  schema_version?: SchemaVersion;
  rewind_id: RewindId;
  massif_id: MassifId;
  start: Start;
  end: End;
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
  [k: string]: DiamondRewindKpi;
}
export interface DiamondRewindKpi {
  kpi_id: KpiId;
  aggregator_version: AggregatorVersion;
  unit: Unit;
  ranking: Ranking;
}
export interface DiamondRewindEntry {
  station_id: StationId;
  value: Value;
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
