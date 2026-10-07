/* Generated from config/schemas/layout.schema.json by `npm run gen:types`. Do not edit. */

/**
 * Live tile of config/tiles.yaml.
 */
export type Tile = string;
/**
 * Period shown (today's, or tomorrow's once today's is over).
 */
export type Period = string;
/**
 * Home page tiles in priority order: the first one is shown first.
 */
export type Home = HomeTile[];
export type Default = string[];

/**
 * Schema of ``config/layout.yaml``: home page and tile order, optionally per massif.
 */
export interface LayoutFile {
  home?: Home;
  default: Default;
  overrides?: Overrides;
}
/**
 * A tile of the home page (no filter selected), for one of its periods.
 */
export interface HomeTile {
  tile: Tile;
  period: Period;
}
export interface Overrides {
  [k: string]: string[];
}
