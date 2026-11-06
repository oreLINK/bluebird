/* Generated from config/schemas/layout.schema.json by `npm run gen:types`. Do not edit. */

/**
 * scored: pinned tiles, alerts, then by visibility; fixed: pinned + fallback.
 */
export type Mode = 'scored' | 'fixed';
/**
 * Live tile of config/tiles.yaml.
 */
export type Tile = string;
/**
 * Period shown (today's, or tomorrow's once today's is over).
 */
export type Period = string;
/**
 * Always first, whatever their score, in this order.
 */
export type Pinned = HomeTile[];
/**
 * Shown after the pinned tiles in `fixed` mode, or when no tile is significant.
 */
export type Fallback = HomeTile[];
/**
 * Most tiles on the home page, pinned included (the footer stays reachable).
 */
export type Limit = number;
/**
 * Stations averaged by the measure.
 */
export type Top = number;
export type Current = number;
export type Next = number;
export type Later = number;
/**
 * Local time, on the ski day clock.
 */
export type From = string;
export type Factor = number;
/**
 * @minItems 1
 */
export type Steps = [RelevanceStep, ...RelevanceStep[]];
export type First = number;
export type Later1 = number;
/**
 * @minItems 1
 */
export type Filters = [string, ...string[]];
export type From1 = string;
export type Factor1 = number;
export type High = number;
export type Medium = number;
export type Low = number;
/**
 * Multiplier for stale values.
 */
export type Stale = number;
/**
 * Share of the place's stations with a value.
 */
export type CoverageMin = number;
/**
 * Multiplier below `coverage_min`.
 */
export type Coverage = number;
export type First1 = number;
export type PerCategory = number;
export type Default = string[];

/**
 * Schema of ``config/layout.yaml``: home page and tile order, optionally per massif.
 */
export interface LayoutFile {
  home?: HomePage;
  default: Default;
  overrides?: Overrides;
}
/**
 * Home page: pinned tiles, then tiles ranked by their visibility score.
 */
export interface HomePage {
  mode?: Mode;
  pinned?: Pinned;
  fallback?: Fallback;
  limit?: Limit;
  top?: Top;
  relevance?: HomeRelevance | null;
  reliability?: HomeReliability;
  diversity?: HomeDiversity;
}
/**
 * A tile of the home page (no filter selected), for one of its periods.
 */
export interface HomeTile {
  tile: Tile;
  period: Period;
}
/**
 * Relevance factor of a candidate tile by the time of day (ski day clock).
 */
export interface HomeRelevance {
  slots?: SlotRelevance;
  today: Today;
  tomorrow: TomorrowRelevance;
  early_alerts?: EarlyAlerts | null;
}
/**
 * Relevance of today's time slots: in progress, the next one, the later ones.
 */
export interface SlotRelevance {
  current?: Current;
  next?: Next;
  later?: Later;
}
/**
 * Steps of today's day-grain periods (day, sunset, overnight) by local time.
 */
export interface Today {
  /**
   * @minItems 1
   *
   * This interface was referenced by `Today`'s JSON-Schema definition
   * via the `patternProperty` "^[a-z0-9]+(?:[_-][a-z0-9]+)*$".
   */
  [k: string]: [RelevanceStep, ...RelevanceStep[]];
}
/**
 * From local time `from`, the relevance factor is `factor` (until the next step).
 */
export interface RelevanceStep {
  from: From;
  factor: Factor;
}
/**
 * Relevance of tomorrow's tiles: 0 before the first step, then step x period factor.
 */
export interface TomorrowRelevance {
  steps: Steps;
  slots?: TomorrowSlots;
}
/**
 * Factor of tomorrow's time slots: the first one of the day, the others.
 */
export interface TomorrowSlots {
  first?: First;
  later?: Later1;
}
/**
 * Tomorrow's alerts of these filters show from `from` (before the tomorrow steps).
 */
export interface EarlyAlerts {
  filters: Filters;
  from: From1;
  factor: Factor1;
}
/**
 * Reliability factor: confidence of the top stations, stale data, station coverage.
 */
export interface HomeReliability {
  high?: High;
  medium?: Medium;
  low?: Low;
  stale?: Stale;
  coverage_min?: CoverageMin;
  coverage?: Coverage;
}
/**
 * At most `per_category` tiles of one category among the first `first` ranked tiles.
 */
export interface HomeDiversity {
  first?: First1;
  per_category?: PerCategory;
}
export interface Overrides {
  [k: string]: string[];
}
