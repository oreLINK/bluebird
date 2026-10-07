/* Generated from config/schemas/rewinds.schema.json by `npm run gen:types`. Do not edit. */

/**
 * Season id, e.g. 2025-26; also the folder in config/rewind/.
 */
export type Id = string;
export type Fr = string;
export type En = string;
/**
 * First day of the season (local), included.
 */
export type Start = string;
/**
 * Last day of the season (local), included.
 */
export type End = string;
/**
 * @minItems 1
 */
export type Massifs = [string, ...string[]];
/**
 * Historical KPIs of this Rewind.
 *
 * @minItems 1
 */
export type Kpis = [string, ...string[]];
/**
 * Level-1 filter (config/filters.yaml) showing its tiles (no levels).
 */
export type Filter = string;
export type Enabled = boolean;
export type Rewinds = Rewind[];

/**
 * Schema of ``config/rewinds.yaml``.
 */
export interface RewindsFile {
  rewinds?: Rewinds;
}
/**
 * A Rewind: the review of a closed ski season, ranked on historical KPIs.
 */
export interface Rewind {
  id: Id;
  name: Localized;
  start: Start;
  end: End;
  massifs: Massifs;
  kpis: Kpis;
  filter: Filter;
  enabled?: Enabled;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized {
  fr: Fr;
  en: En;
}
