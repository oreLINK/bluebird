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
export type Es = string;
/**
 * Value (in `unit`) of a full bar in the tiles, e.g. 100 for a percentage. Default: the best value of the ranking.
 */
export type Max = number | null;
export type Kind1 = 'percent' | 'value' | 'levels' | 'scale';
/**
 * value: driver holding the median; scale: the level.
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
 * The level, as held by the display `driver`.
 */
export type Value = number;
/**
 * Colour of the level on the tiles (`--scale-<tone>-*` tokens in tokens.css).
 */
export type Tone = 'danger-1' | 'danger-2' | 'danger-3' | 'danger-4' | 'danger-5';
/**
 * scale: the levels, by increasing `value`.
 */
export type Steps = ScaleStep[];
/**
 * Driver shown in small type.
 */
export type Note = string | null;
/**
 * Ranking order: desc puts the highest value first; asc the lowest (e.g. fewest white days).
 */
export type Order = 'desc' | 'asc';
export type Enabled = boolean;
/**
 * The value is relayed as is from an official source (e.g. the Météo-France avalanche bulletin), never computed by Bluebird: a blue rosette next to the tile title, explained on the back.
 */
export type Certified = boolean;
/**
 * Official page (e.g. the avalanche bulletins), new tab.
 */
export type Url = string;
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
/**
 * Below it (top-3 mean) the tile is not significant.
 */
export type Floor = number;
/**
 * At or beyond it the impact is full (1).
 */
export type Strong = number;
/**
 * Editorial weight of the KPI (0..1].
 */
export type Priority = number;
/**
 * value (needs a `value` display) or probability; default from the display.
 */
export type Measure = ('value' | 'probability') | null;
/**
 * Measure at or beyond which the tile is an alert: shown right after the pinned tiles (and, for the `early_alerts` filters of layout.yaml, tomorrow from noon).
 */
export type Alert = number | null;
/**
 * Below it (top-3 mean) the tile is not significant.
 */
export type Floor1 = number;
/**
 * At or beyond it the impact is full (1).
 */
export type Strong1 = number;
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
  certified?: Certified;
  /**
   * certified KPIs: the official page to read the source itself (e.g. the full avalanche bulletin), linked from the back of the tiles, opened in a new tab.
   */
  official_link?: OfficialLink | null;
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
  /**
   * Live KPIs: priority and significance thresholds of the home page visibility score; without it the KPI is never ranked on the home page.
   */
  visibility?: KpiVisibility | null;
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
  es: Es;
}
/**
 * Live KPIs: shown as a percent (default), a value, levels or a scale.
 */
export interface KpiDisplay {
  kind?: Kind1;
  driver?: Driver;
  range?: Range;
  tolerance?: Tolerance;
  bands?: Bands;
  levels?: Levels;
  steps?: Steps;
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
/**
 * A step of a `scale` display: one level of an official scale (e.g. avalanche danger 4).
 */
export interface ScaleStep {
  value: Value;
  tone: Tone;
  label: Localized1;
  /**
   * What to do at this level, shown on the tile back.
   */
  advice?: Localized | null;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized1 {
  fr: Fr;
  en: En;
  es: Es;
}
/**
 * Link from the back of a `certified` KPI's tiles to the official source itself.
 */
export interface OfficialLink {
  url: Url;
  label: Localized2;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized2 {
  fr: Fr;
  en: En;
  es: Es;
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
/**
 * How a live KPI competes for the home page (visibility score, README.md).
 *
 * The measure is the mean of the top 3 stations of the chosen place: the
 * median value of the display `driver` (`value`) or the probability
 * (`probability`, 0..1). Impact = (measure - floor) / (strong - floor),
 * clamped to 0..1; `strong` below `floor` means lower is stronger (e.g. a
 * colder wind chill). Below `floor` the tile is hidden from the home page.
 */
export interface KpiVisibility {
  floor: Floor;
  strong: Strong;
  priority: Priority;
  measure?: Measure;
  alert?: Alert;
  /**
   * `floor` and `strong` for the time slots, when they differ from the day's.
   */
  slots?: SlotThresholds | null;
}
/**
 * Significance thresholds of a live KPI for its time slots (morning, afternoon…).
 */
export interface SlotThresholds {
  floor: Floor1;
  strong: Strong1;
}
