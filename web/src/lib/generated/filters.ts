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
 * Levels offered once this filter is chosen, in order: `group` (its `groups`), `day` (today, tomorrow), `slot` (morning, evening…). Live KPIs only.
 *
 * @maxItems 3
 */
export type Levels =
  | []
  | ['group' | 'day' | 'slot']
  | ['group' | 'day' | 'slot', 'group' | 'day' | 'slot']
  | ['group' | 'day' | 'slot', 'group' | 'day' | 'slot', 'group' | 'day' | 'slot'];
export type Id1 = string;
export type Icon1 = string | null;
/**
 * KPIs of the sub-category.
 *
 * @minItems 1
 */
export type Kpis = [string, ...string[]];
/**
 * Sub-categories for the `group` level; every KPI of the filter in one.
 */
export type Groups = FilterGroup[];

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
  groups?: Groups;
}
/**
 * A user-facing string in every supported UI language.
 */
export interface Localized {
  fr: Fr;
  en: En;
}
/**
 * A sub-category of a level-1 filter (level `group`), e.g. Poudreuse under Glisse.
 */
export interface FilterGroup {
  id: Id1;
  name: Localized;
  icon?: Icon1;
  kpis: Kpis;
}
