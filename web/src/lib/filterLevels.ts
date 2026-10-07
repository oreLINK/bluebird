/**
 * Filter levels of the filter bar, Spotify-style (unit-tested).
 *
 * The selection is a path: `[]` (home), `['snow']`, `['snow', 'd0']`,
 * `['snow', 'd0', 'morning']`. Level 1 is a filter of config/filters.yaml;
 * the next levels are the `levels` of that filter, built-in kinds:
 *   day   ski day of the tile (`d0` today, `d1` tomorrow; `days` labels of
 *         config/periods.yaml)
 *   slot  time slot of the tile (periods without `native_window`, `chip`
 *         labels); whole-day tiles are under no slot.
 * The bar shows the chosen chips (pressed, removable), then the options of the
 * next level, only those that still have tiles. With nothing chosen it shows
 * every level-1 filter and the page shows each filter's `overview` tile.
 *
 * A new kind of level is one entry of LEVEL_KINDS plus its value in
 * `FilterLevel` (pipeline config.py).
 */
import {
  type Filter,
  type ResolvedTile,
  type Rewind,
  filterTiles,
  rewindOfFilter,
  usableFilters,
} from './config';
import type { MassifDaily } from './data';
import type { Localized } from './generated/filters';
import {
  type Period,
  type TileInstance,
  daysBetween,
  expandTiles,
  periodsFile,
  referenceDay,
} from './periods';

export type LevelKind = NonNullable<Filter['levels']>[number];

/** A chip of the filter bar. */
export interface FilterChip {
  /** Unique in the bar: `<level>:<id>`. */
  key: string;
  /** Path item: filter id, `d0`, `morning`… */
  id: string;
  /** 1 = topic (config/filters.yaml), 2.. = its levels. */
  level: number;
  name: Localized;
  icon?: string | null;
  theme?: Filter['theme'];
  /** Chosen: filled, with a × that removes it and the levels after it. */
  pressed: boolean;
}

export interface FilterState {
  /** The path actually applied (unknown or stale items dropped). */
  path: string[];
  chips: FilterChip[];
  /** Configured tiles of the selection (placeholders while live data loads). */
  tiles: ResolvedTile[];
  /** Tiles to show, one per period for live tiles. */
  instances: TileInstance[];
  /** The Rewind of the chosen level-1 filter, if any. */
  rewind?: Rewind;
}

interface LevelContext {
  refDay: string;
  periods: Period[];
  days: Localized[];
}

interface LevelOption {
  id: string;
  name: Localized;
}

interface LevelKindSpec {
  /** Options offered for these tiles, in display order. */
  options: (instances: TileInstance[], ctx: LevelContext) => LevelOption[];
  match: (instance: TileInstance, optionId: string, ctx: LevelContext) => boolean;
}

const dayId = (instance: TileInstance, ctx: LevelContext): string | null =>
  instance.slot ? `d${daysBetween(ctx.refDay, instance.slot.skiDay)}` : null;

export const LEVEL_KINDS: Record<LevelKind, LevelKindSpec> = {
  day: {
    options: (instances, ctx) =>
      ctx.days.flatMap((name, offset) =>
        instances.some((i) => dayId(i, ctx) === `d${offset}`) ? [{ id: `d${offset}`, name }] : [],
      ),
    match: (instance, id, ctx) => dayId(instance, ctx) === id,
  },
  slot: {
    options: (instances, ctx) =>
      ctx.periods.flatMap((p) =>
        !p.native_window && p.chip && instances.some((i) => i.slot?.periodId === p.id)
          ? [{ id: p.id, name: p.chip }]
          : [],
      ),
    match: (instance, id) => instance.slot?.periodId === id,
  },
};

const chip = (filter: Filter, pressed: boolean): FilterChip => ({
  key: `1:${filter.id}`,
  id: filter.id,
  level: 1,
  name: filter.name,
  icon: filter.icon,
  theme: filter.theme,
  pressed,
});

/** What the filter bar and the page show for a selection path. */
export function filterState(
  path: string[],
  filters: Filter[],
  resolved: ResolvedTile[],
  payload: MassifDaily | null,
  now: number,
  periods: Period[] = periodsFile.periods,
  days: Localized[] = periodsFile.days ?? [],
): FilterState {
  const bar = usableFilters(filters, resolved);
  const topic = bar.find((f) => f.id === path[0]);

  if (!topic) {
    const tiles: ResolvedTile[] = [];
    const instances: TileInstance[] = [];
    for (const { overview } of bar) {
      const tile = resolved.find((r) => r.tile.id === overview?.tile);
      if (!overview || !tile) continue;
      tiles.push(tile);
      const instance = expandTiles([tile], payload, now, periods).find(
        (i) => i.slot?.periodId === overview.period,
      );
      if (instance) instances.push(instance);
    }
    return { path: [], chips: bar.map((f) => chip(f, false)), tiles, instances };
  }

  const tiles = filterTiles(resolved, topic);
  let instances = expandTiles(tiles, payload, now, periods);
  const ctx: LevelContext = { refDay: payload ? referenceDay(payload, now) : '', periods, days };
  const kept = [topic.id];
  const chips = [chip(topic, true)];
  for (const [index, kind] of (topic.levels ?? []).entries()) {
    const spec = LEVEL_KINDS[kind];
    const level = index + 2;
    const options = spec.options(instances, ctx);
    const chosen = options.find((o) => o.id === path[index + 1]);
    if (!chosen) {
      chips.push(...options.map((o) => ({ key: `${level}:${o.id}`, ...o, level, pressed: false })));
      break;
    }
    instances = instances.filter((i) => spec.match(i, chosen.id, ctx));
    kept.push(chosen.id);
    chips.push({ key: `${level}:${chosen.id}`, ...chosen, level, pressed: true });
  }
  return { path: kept, chips, tiles, instances, rewind: rewindOfFilter(topic.id) };
}

/**
 * The path after a tap on a chip: a pressed chip is removed with the levels
 * after it; another chip is chosen at its level.
 */
export function nextPath(path: string[], tapped: FilterChip): string[] {
  const before = path.slice(0, tapped.level - 1);
  return tapped.pressed ? before : [...before, tapped.id];
}
