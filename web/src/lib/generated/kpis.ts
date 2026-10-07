/* Generated from config/schemas/kpis.schema.json by `npm run gen:types`. Do not edit. */

export type Id = string;
/**
 * Id of a registered gold Aggregator.
 */
export type Aggregator = string;
/**
 * live: probability for today, computed by the daily run; historical: value over a past season, computed by `bluebird rewind` (config/rewinds.yaml).
 */
export type Kind = 'live' | 'historical';
export type Unit = string;
export type Decimals = number;
/**
 * Multiplier from the aggregator's unit (cm for snow, h for durations) to `unit`, e.g. 0.01 to publish centimetres as metres.
 */
export type Scale = number;
export type Fr = string;
export type En = string;
/**
 * Value (in `unit`) of a full bar in the tiles, e.g. 100 for a percentage. Default: the best value of the ranking.
 */
export type Max = number | null;
export type Kind1 = 'percent' | 'value' | 'levels';
/**
 * value: driver holding the median.
 */
export type Driver = string | null;
/**
 * value: p10 and p90 drivers.
 */
export type Range = [string, string] | null;
/**
 * value: p90 - p10 spread of a high reliability.
 */
export type Tolerance = number | null;
export type Max1 = number | null;
export type Bands = DisplayBand[];
export type Min = number;
export type Levels = DisplayLevel[];
/**
 * Driver shown in small type.
 */
export type Note = string | null;
/**
 * Ranking order: desc puts the highest value first; asc the lowest (e.g. fewest white days).
 */
export type Order = 'desc' | 'asc';
export type Enabled = boolean;
export type Unit1 = string | null;
export type Decimals1 = number;
/**
 * Ids of the filters (config/filters.yaml) this KPI appears under.
 */
export type Filters = string[];
/**
 * Ids of the periods (config/periods.yaml) a live KPI is computed for; ignored for historical KPIs.
 *
 * @minItems 1
 */
export type Periods = [string, ...string[]];
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
  kind?: Kind;
  /**
   * Unit and decimals of the value; required for historical KPIs.
   */
  value?: ValueSpec | null;
  display?: KpiDisplay;
  order?: Order;
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
  periods?: Periods;
}
/**
 * Unit of the value of a historical KPI, as published and displayed (e.g. 4.43 m).
 */
export interface ValueSpec {
  unit: Unit;
  decimals?: Decimals;
  scale?: Scale;
  /**
   * Unit as shown on the site when it differs by language (e.g. jours / days).
   */
  unit_label?: Localized | null;
  /**
   * Singular of `unit_label` (e.g. jour / day), used where the language says so.
   */
  unit_label_one?: Localized | null;
  max?: Max;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized {
  fr: Fr;
  en: En;
}
/**
 * Live KPIs: shown as a percent (default), a value or levels.
 */
export interface KpiDisplay {
  kind?: Kind1;
  driver?: Driver;
  range?: Range;
  tolerance?: Tolerance;
  bands?: Bands;
  levels?: Levels;
  note?: Note;
}
/**
 * A named band of a `value` display, for values up to `max` (none: every value above).
 */
export interface DisplayBand {
  max?: Max1;
  label: Localized;
}
/**
 * A level of a `levels` display, shown from probability `min` (e.g. Oui from 0.6).
 */
export interface DisplayLevel {
  min: Min;
  label: Localized;
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
  unit?: Unit1;
  decimals?: Decimals1;
}
