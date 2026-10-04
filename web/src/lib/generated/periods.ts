/* Generated from config/schemas/periods.schema.json by `npm run gen:types`. Do not edit. */

/**
 * Local time a ski day starts: ski day D runs from D day_start to D+1.
 */
export type DayStart = string;
/**
 * Ski days published: 1 = today, 2 = + tomorrow.
 */
export type HorizonDays = number;
/**
 * @minItems 1
 */
export type Periods = [Period, ...Period[]];
export type Id = string;
export type Start = string;
/**
 * '00:00' after a later start means midnight.
 */
export type End = string;
/**
 * The KPI computes over its own window (e.g. the whole ski day); `start`/`end` then only decide when the period is shown.
 */
export type NativeWindow = boolean;
/**
 * Label per day offset: [today, tomorrow, …], used in tile titles.
 *
 * @minItems 1
 */
export type Labels = [Localized, ...Localized[]];
export type Fr = string;
export type En = string;

/**
 * Schema of ``config/periods.yaml``.
 */
export interface PeriodsFile {
  day_start?: DayStart;
  horizon_days?: HorizonDays;
  periods: Periods;
}
/**
 * A time slot of the ski day a KPI is computed for (morning, evening…).
 */
export interface Period {
  id: Id;
  start: Start;
  end: End;
  native_window?: NativeWindow;
  labels: Labels;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized {
  fr: Fr;
  en: En;
}
