/* Generated from config/schemas/filters.schema.json by `npm run gen:types`. Do not edit. */

/**
 * @minItems 1
 */
export type Filters = [Filter, ...Filter[]];
export type Id = string;
export type Fr = string;
export type En = string;
export type Es = string;
export type Icon = string | null;
/**
 * Colour of the chip (rewind: Christmas red; mood: moving multicolour text and border).
 */
export type Theme = 'default' | 'rewind' | 'mood';
/**
 * Levels offered once this filter is chosen, in order: `group` (its `groups`), `day` (today, tomorrow), `slot` (morning, evening…). Live KPIs only.
 *
 * @maxItems 3
 */
export type Levels =
  | []
  | ['group' | 'day' | 'slot' | 'mood_group' | 'mood']
  | [
      'group' | 'day' | 'slot' | 'mood_group' | 'mood',
      'group' | 'day' | 'slot' | 'mood_group' | 'mood'
    ]
  | [
      'group' | 'day' | 'slot' | 'mood_group' | 'mood',
      'group' | 'day' | 'slot' | 'mood_group' | 'mood',
      'group' | 'day' | 'slot' | 'mood_group' | 'mood'
    ];
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
export type Id2 = string;
export type Icon2 = string | null;
/**
 * Show tomorrow's periods only, at any time of day (e.g. Je monte demain).
 */
export type TomorrowOnly = boolean;
/**
 * @minItems 1
 */
export type Moods1 = [Mood, ...Mood[]];
export type Id3 = string;
export type Icon3 = string | null;
/**
 * Live KPIs shown under this mood.
 *
 * @minItems 1
 */
export type Kpis1 = [string, ...string[]];
/**
 * Sub-moods and moods for the `mood_group` and `mood` levels; the filter then shows the KPIs of its moods (no `filters:` tag needed).
 */
export type Moods = MoodGroup[];

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
  moods?: Moods;
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
 * A sub-category of a level-1 filter (level `group`), e.g. Poudreuse under Glisse.
 */
export interface FilterGroup {
  id: Id1;
  name: Localized;
  icon?: Icon1;
  kpis: Kpis;
}
/**
 * A sub-mood (level `mood_group`), e.g. Sur place or En route, and its moods.
 */
export interface MoodGroup {
  id: Id2;
  name: Localized;
  icon?: Icon2;
  tomorrow_only?: TomorrowOnly;
  moods: Moods1;
}
/**
 * A mood (level `mood`), e.g. Freerider: the KPIs that matter for that wish of the day.
 *
 * Unlike groups, a KPI can belong to several moods; the page shows all of them,
 * ordered by the home page visibility score (lib/homeFeed.ts).
 */
export interface Mood {
  id: Id3;
  name: Localized;
  icon?: Icon3;
  kpis: Kpis1;
}
