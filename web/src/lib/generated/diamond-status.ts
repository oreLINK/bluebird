/* Generated from config/schemas/diamond-status.schema.json by `npm run gen:types`. Do not edit. */

export type SchemaVersion = 1;
/**
 * Start of the refresh.
 */
export type GeneratedAt = string;
export type RunId = string;
export type SkiDay = string;
/**
 * Most degraded state of everything below.
 */
export type State = 'ok' | 'partial' | 'stale' | 'down';
/**
 * Source id from config/sources.yaml.
 */
export type Id = string;
/**
 * Silver dataset produced (transformations only).
 */
export type Dataset = string | null;
export type State1 = 'ok' | 'partial' | 'stale' | 'down';
/**
 * Stations with data, when known.
 */
export type Ok = number | null;
export type Expected = number | null;
export type Sources = DiamondStatusItem[];
export type Transforms = DiamondStatusItem[];
/**
 * KPI id from config/kpis.yaml.
 */
export type Id1 = string;
/**
 * Most degraded state of its periods.
 */
export type State2 = 'ok' | 'partial' | 'stale' | 'down';
export type Key = string;
export type PeriodId = string;
export type SkiDay1 = string;
/**
 * Local time, with UTC offset.
 */
export type Start = string;
/**
 * Local time, with UTC offset. Over afterwards.
 */
export type End = string;
export type State3 = 'ok' | 'partial' | 'stale' | 'down';
/**
 * Stations with a value.
 */
export type Ok1 = number;
export type Expected1 = number;
/**
 * When the values shown were computed.
 */
export type UpdatedAt = string | null;
export type Periods = DiamondStatusPeriod[];
export type Kpis = DiamondStatusKpi[];
/**
 * Tile id from config/tiles.yaml.
 */
export type TileId = string;

/**
 * ``diamond/status.json``: health of the last refresh, shown in the site footer.
 */
export interface DiamondStatus {
  schema_version?: SchemaVersion;
  generated_at: GeneratedAt;
  run_id: RunId;
  ski_day: SkiDay;
  state: State;
  sources: Sources;
  transforms: Transforms;
  kpis: Kpis;
  tiles: Tiles;
}
/**
 * State of one source (bronze) or one transformation (silver).
 */
export interface DiamondStatusItem {
  id: Id;
  dataset: Dataset;
  state: State1;
  ok: Ok;
  expected: Expected;
}
export interface DiamondStatusKpi {
  id: Id1;
  state: State2;
  periods: Periods;
}
/**
 * State of one KPI, or one tile, for one period of one ski day.
 */
export interface DiamondStatusPeriod {
  key: Key;
  period_id: PeriodId;
  ski_day: SkiDay1;
  start: Start;
  end: End;
  state: State3;
  ok: Ok1;
  expected: Expected1;
  updated_at: UpdatedAt;
}
/**
 * Per massif id.
 */
export interface Tiles {
  [k: string]: DiamondStatusTile[];
}
export interface DiamondStatusTile {
  tile_id: TileId;
  period: DiamondStatusPeriod;
}
