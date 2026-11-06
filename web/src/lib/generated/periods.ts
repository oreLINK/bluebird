/* Generated from config/schemas/periods.schema.json by `npm run gen:types`. Do not edit. */

/**
 * Local time a ski day starts: ski day D runs from D day_start to D+1.
 */
export type DayStart = string;
/**
 * Ski days published: 1 = today, 2 = + tomorrow.
 */
export type HorizonDays = number;
export type Fr = string;
export type En = string;
export type Es = string;
/**
 * Chips of the `day` filter level, one per day of the horizon: [today, …].
 */
export type Days = Localized[];
export type Tone = 'today' | 'tonight' | 'tomorrow';
/**
 * Day cell of the tile time badge, one per day of the horizon: [today, …].
 */
export type BadgeDays = BadgeDay[];
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
 * Label per day offset: [today, tomorrow, …], where the period is written out (tile back, screen readers, service status).
 *
 * @minItems 1
 */
export type Labels = [Localized, ...Localized[]];
/**
 * Colour of the moment cell; required with `badge`. Today, a `night` tone shows `badge_tonight` alone ('Cette nuit').
 */
export type Tone1 = ('morning' | 'midday' | 'afternoon' | 'evening' | 'night') | null;

/**
 * Schema of ``config/periods.yaml``.
 */
export interface PeriodsFile {
  day_start?: DayStart;
  horizon_days?: HorizonDays;
  days?: Days;
  badge_days?: BadgeDays;
  /**
   * Replaces today + a `night` moment on the time badge, in one cell ('Cette nuit').
   */
  badge_tonight?: BadgeDay | null;
  periods: Periods;
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
 * Day cell of the tile time badge: a short label in the colour of the day.
 */
export interface BadgeDay {
  tone: Tone;
  label: Localized;
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
  /**
   * Chip of the `slot` filter level (Matin, Soir…); required for time slots.
   */
  chip?: Localized | null;
  /**
   * Short moment cell of the tile time badge, beside the day ('Matin', 'PM'); none for a whole-day period, whose badge shows the day alone.
   */
  badge?: Localized | null;
  tone?: Tone1;
}
