/* Generated from config/schemas/kpis.schema.json by `npm run gen:types`. Do not edit. */

export type Id = string;
/**
 * Id of a registered gold Aggregator.
 */
export type Aggregator = string;
export type Enabled = boolean;
export type Fr = string;
export type En = string;
export type Unit = string | null;
export type Decimals = number;
/**
 * Ids of the filters (config/filters.yaml) this KPI appears under.
 */
export type Filters = string[];
export type Kpis = Kpi[];

/**
 * Schema of ``config/kpis.yaml``.
 */
export interface KpisFile {
  kpis: Kpis;
}
/**
 * A KPI computed by a gold-layer Aggregator.
 */
export interface Kpi {
  id: Id;
  aggregator: Aggregator;
  enabled?: Enabled;
  name: Localized;
  description: Localized;
  /**
   * How the KPI is computed, in plain words, shown on the back of its tiles. `{param}` placeholders are replaced by the values of `params`.
   */
  method?: Localized | null;
  params?: Params;
  drivers?: Drivers;
  filters?: Filters;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized {
  fr: Fr;
  en: En;
}
export interface Params {
  [k: string]: unknown;
}
export interface Drivers {
  [k: string]: DriverSpec;
}
/**
 * How to display one explanatory value attached to a KPI result.
 */
export interface DriverSpec {
  label: Localized;
  unit?: Unit;
  decimals?: Decimals;
}
