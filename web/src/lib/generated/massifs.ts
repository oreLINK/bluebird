/* Generated from config/schemas/massifs.schema.json by `npm run gen:types`. Do not edit. */

export type Id = string;
export type Fr = string;
export type En = string;
export type Timezone = string;
export type Enabled = boolean;
/**
 * Sort order in the site menu.
 */
export type Order = number;
/**
 * [min_lon, min_lat, max_lon, max_lat]
 *
 * @minItems 4
 * @maxItems 4
 */
export type Bbox = [number, number, number, number];
/**
 * Relative ridge heights (0..1), west to east, for the banner illustrations.
 */
export type Skyline = number[];
export type Id1 = string;
/**
 * ISO 3166-1 alpha-2 code of the zone's country.
 */
export type Country = string;
/**
 * Département number, e.g. '65'.
 */
export type Code = string | null;
/**
 * Sub-massifs (level 2 of the massif bar); every station names one.
 */
export type Zones = Zone[];
export type Massifs = Massif[];

/**
 * Schema of ``config/massifs.yaml``.
 */
export interface MassifsFile {
  massifs: Massifs;
}
/**
 * A mountain range grouping several stations.
 */
export interface Massif {
  id: Id;
  name: Localized;
  timezone?: Timezone;
  enabled?: Enabled;
  order?: Order;
  bbox: Bbox;
  skyline?: Skyline;
  zones?: Zones;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized {
  fr: Fr;
  en: En;
}
/**
 * A sub-massif (level 2 of the massif bar): a French département, or abroad a
 * country or region (Andorre, Aragon, Valais…).
 */
export interface Zone {
  id: Id1;
  name: Localized;
  country?: Country;
  code?: Code;
}
