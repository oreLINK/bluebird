/* Generated from config/schemas/tiles.schema.json by `npm run gen:types`. Do not edit. */

export type Id = string;
/**
 * `ranking`: every station ranked on one KPI (`station`: planned).
 */
export type Scope = 'ranking';
/**
 * `full`: the image fills the card; `banner`: image band on top; `compact`: no image, half the height of a banner tile.
 */
export type Format = 'full' | 'banner' | 'compact';
/**
 * Image of a `full` or `banner` tile: `scene` (illustration, option `scene`) or `photo` (photo of the leading station, else the illustration).
 */
export type Visual = 'scene' | 'photo';
/**
 * Webcam positions that suit the KPI, by preference (first match wins).
 *
 * @minItems 1
 */
export type Positions = [
  'summit' | 'slopes' | 'village' | 'nordic',
  ...('summit' | 'slopes' | 'village' | 'nordic')[]
];
/**
 * Probability the leading station needs for the webcam link to show.
 */
export type MinProbability = number;
export type Kpis = string[];
export type Fr = string;
export type En = string;
export type Es = string;
export type Icon = string | null;
/**
 * Periods to show a tile of live KPIs for; defaults to every period of its KPIs.
 */
export type Periods = string[] | null;
export type Tiles = Tile[];

/**
 * Schema of ``config/tiles.yaml``.
 */
export interface TilesFile {
  tiles: Tiles;
}
/**
 * A KPI container displayed on the page.
 *
 * Tiles are classified on three axes: `scope` (how many stations), `format`
 * (size and layout) and `visual` (background of the image). Whether they show
 * forecasts or a past season comes from the `kind` of their KPIs.
 */
export interface Tile {
  id: Id;
  scope?: Scope;
  format: Format;
  visual?: Visual;
  /**
   * Live tiles of format `full` or `banner`: a LIVE badge links the webcam of the leading station while today's period is in progress.
   */
  webcam?: TileWebcam | null;
  kpis?: Kpis;
  /**
   * Defaults to the first KPI's name. Never contains the period: the site shows it on the time badge of each tile instance (day + moment, `config/periods.yaml`).
   */
  title?: Localized | null;
  icon?: Icon;
  periods?: Periods;
  options?: Options;
}
/**
 * When a tile links the live webcam of its leading station (today only).
 */
export interface TileWebcam {
  positions: Positions;
  min_probability?: MinProbability;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized {
  fr: Fr;
  en: En;
  es: Es;
}
export interface Options {
  [k: string]: unknown;
}
