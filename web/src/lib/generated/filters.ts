/* Generated from config/schemas/filters.schema.json by `npm run gen:types`. Do not edit. */

/**
 * @minItems 1
 */
export type Filters = [Filter, ...Filter[]];
export type Id = string;
export type Fr = string;
export type En = string;
export type Icon = string | null;
/**
 * Show every tile, whatever its KPIs.
 */
export type All = boolean;

/**
 * Schema of ``config/filters.yaml``: the filter bar, in display order.
 */
export interface FiltersFile {
  filters: Filters;
}
/**
 * A chip of the filter bar: shows the tiles of the KPIs tagged with its id.
 */
export interface Filter {
  id: Id;
  name: Localized;
  icon?: Icon;
  all?: All;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized {
  fr: Fr;
  en: En;
}
