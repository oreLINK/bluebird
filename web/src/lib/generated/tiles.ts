/* Generated from config/schemas/tiles.schema.json by `npm run gen:types`. Do not edit. */

export type Id = string;
/**
 * Frontend tile component id (web/src/tiles/registry.ts).
 */
export type Type = string;
export type Kpis = string[];
export type Fr = string;
export type En = string;
export type Icon = string | null;
/**
 * Periods to show a tile for; defaults to every period of its KPIs.
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
 */
export interface Tile {
  id: Id;
  type: Type;
  kpis?: Kpis;
  /**
   * Defaults to the first KPI's name. Must contain `{period}`, replaced by the period label (e.g. 'Neige {period}' -> 'Neige ce soir').
   */
  title?: Localized | null;
  icon?: Icon;
  periods?: Periods;
  options?: Options;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized {
  fr: Fr;
  en: En;
}
export interface Options {
  [k: string]: unknown;
}
