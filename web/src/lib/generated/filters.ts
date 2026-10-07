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
 * Colour of the chip (rewind: Christmas red).
 */
export type Theme = 'default' | 'rewind';
/**
 * Levels offered once this filter is chosen, in order: `day` (today, tomorrow), `slot` (morning, evening…). Live KPIs only.
 *
 * @maxItems 3
 */
export type Levels =
  | []
  | ['day' | 'slot']
  | ['day' | 'slot', 'day' | 'slot']
  | ['day' | 'slot', 'day' | 'slot', 'day' | 'slot'];
/**
 * Live tile of config/tiles.yaml with a KPI of this filter.
 */
export type Tile = string;
/**
 * Period shown (today's, or tomorrow's once today's is over).
 */
export type Period = string;

/**
 * Schema of ``config/filters.yaml``: the filter bar, in display order.
 */
export interface FiltersFile {
  filters: Filters;
}
/**
 * A level-1 chip of the filter bar: shows the tiles of the KPIs tagged with its id.
 */
export interface Filter {
  id: Id;
  name: Localized;
  icon?: Icon;
  theme?: Theme;
  levels?: Levels;
  /**
   * Its tile on the home page; none: not on the home page.
   */
  overview?: FilterOverview | null;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized {
  fr: Fr;
  en: En;
}
/**
 * The tile a level-1 filter shows on the home page (no filter selected).
 */
export interface FilterOverview {
  tile: Tile;
  period: Period;
}
