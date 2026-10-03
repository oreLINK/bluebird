/* Generated from config/schemas/diamond-manifest.schema.json by `npm run gen:types`. Do not edit. */

export type SchemaVersion = 1;
export type GeneratedAt = string;
export type ForecastDate = string;
export type GeneratedAt1 = string;
/**
 * Path of the latest payload, relative to the diamond root.
 */
export type Latest = string;
/**
 * Path of the dated payload, relative to the diamond root.
 */
export type Archive = string;

/**
 * ``diamond/manifest.json``: latest available payload per massif.
 */
export interface DiamondManifest {
  schema_version?: SchemaVersion;
  generated_at: GeneratedAt;
  massifs: Massifs;
}
export interface Massifs {
  [k: string]: DiamondManifestEntry;
}
export interface DiamondManifestEntry {
  forecast_date: ForecastDate;
  generated_at: GeneratedAt1;
  latest: Latest;
  archive: Archive;
}
