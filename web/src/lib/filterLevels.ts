/**
 * Filter levels of the filter bar, Spotify-style (unit-tested).
 *
 * The selection is a path: `[]` (home), `['snow']`, `['snow', 'snowfall']`,
 * `['snow', 'snowfall', 'd0']`, `['snow', 'snowfall', 'd0', 'morning']`.
 * Level 1 is a filter of config/filters.yaml; the next levels are the
 * `levels` of that filter, built-in kinds:
 *   group sub-category of the filter (its `groups`); skipped (no chip, no
 *         path item) when fewer than two groups have tiles
 *   day   ski day of the tile (`d0` today, `d1` tomorrow; `days` labels of
 *         config/periods.yaml)
 *   slot  time slot of the tile (periods without `native_window`, `chip`
 *         labels); whole-day tiles are under no slot.
 * Grain rule: until a slot is chosen, the page only shows day-grain tiles
 * (periods with `native_window`: today, tonight…) and Rewind tiles; the time
 * slot tiles appear at the slot level only, so the page stays short.
 * The bar shows the chosen chips (pressed, removable), then the options of the
 * next level, only those that still have tiles. With nothing chosen it shows
 * every level-1 filter and the page shows the `home` tiles of
 * config/layout.yaml, in their priority order (the first one at the top).
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
import type { HomeTile } from './generated/layout';
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
  groups: NonNullable<Filter['groups']>;
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

const kpiOf = (instance: TileInstance): string | undefined => instance.kpis[0]?.id;

export const LEVEL_KINDS: Record<LevelKind, LevelKindSpec> = {
  group: {
    options: (instances, ctx) =>
      ctx.groups.flatMap((g) =>
        instances.some((i) => g.kpis.includes(kpiOf(i) ?? '')) ? [{ id: g.id, name: g.name }] : [],
      ),
    match: (instance, id, ctx) =>
      ctx.groups.find((g) => g.id === id)?.kpis.includes(kpiOf(instance) ?? '') ?? false,
  },
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

/**
 * The home page: each `home` tile for its period (today's, or tomorrow's once
 * today's is over), in priority order. Tiles missing from the layout are skipped.
 */
export function homeTiles(
  home: HomeTile[],
  resolved: ResolvedTile[],
  payload: MassifDaily | null,
  now: number,
  periods: Period[] = periodsFile.periods,
): Pick<FilterState, 'tiles' | 'instances'> {
  const tiles: ResolvedTile[] = [];
  const instances: TileInstance[] = [];
  for (const entry of home) {
    const tile = resolved.find((r) => r.tile.id === entry.tile);
    if (!tile) continue;
    if (!tiles.includes(tile)) tiles.push(tile);
    const instance = expandTiles([tile], payload, now, periods).find(
      (i) => i.slot?.periodId === entry.period,
    );
    if (instance) instances.push(instance);
  }
  return { tiles, instances };
}

/** What the filter bar and the page show for a selection path. */
export function filterState(
  path: string[],
  filters: Filter[],
  resolved: ResolvedTile[],
  payload: MassifDaily | null,
  now: number,
  home: HomeTile[] = [],
  periods: Period[] = periodsFile.periods,
  days: Localized[] = periodsFile.days ?? [],
): FilterState {
  const bar = usableFilters(filters, resolved);
  const topic = bar.find((f) => f.id === path[0]);

  if (!topic) {
    const chips = bar.map((f) => chip(f, false));
    return { path: [], chips, ...homeTiles(home, resolved, payload, now, periods) };
  }

  let tiles = filterTiles(resolved, topic);
  let instances = expandTiles(tiles, payload, now, periods);
  const ctx: LevelContext = {
    refDay: payload ? referenceDay(payload, now) : '',
    periods,
    days,
    groups: topic.groups ?? [],
  };
  const kept = [topic.id];
  const chips = [chip(topic, true)];
  let slotChosen = false;
  for (const kind of topic.levels ?? []) {
    const spec = LEVEL_KINDS[kind];
    // Groups are known from the configuration: they narrow the tiles even while live data loads.
    const options =
      kind === 'group'
        ? ctx.groups.filter((g) => tiles.some((t) => g.kpis.includes(t.kpis[0]?.id ?? '')))
        : spec.options(instances, ctx);
    if (kind === 'group' && options.length < 2) continue; // a single sub-category: skipped
    const level = kept.length + 1;
    const chosen = options.find((o) => o.id === path[kept.length]);
    if (!chosen) {
      chips.push(
        ...options.map((o) => ({ key: `${level}:${o.id}`, id: o.id, name: o.name, level, pressed: false })),
      );
      break;
    }
    instances = instances.filter((i) => spec.match(i, chosen.id, ctx));
    if (kind === 'group') {
      const group = ctx.groups.find((g) => g.id === chosen.id);
      tiles = tiles.filter((t) => group?.kpis.includes(t.kpis[0]?.id ?? ''));
    }
    slotChosen ||= kind === 'slot';
    kept.push(chosen.id);
    const { id, name } = chosen;
    chips.push({ key: `${level}:${id}`, id, name, level, pressed: true });
  }
  if (!slotChosen) instances = instances.filter((i) => isDayGrain(i, periods));
  return { path: kept, chips, tiles, instances, rewind: rewindOfFilter(topic.id) };
}

/** A day-grain tile (period with `native_window`) or a Rewind tile (no period). */
export function isDayGrain(instance: TileInstance, periods: Period[] = periodsFile.periods): boolean {
  if (!instance.slot) return true;
  return periods.find((p) => p.id === instance.slot?.periodId)?.native_window === true;
}

/**
 * The path after a tap on a chip: a pressed chip is removed with the levels
 * after it; another chip is chosen at its level.
 */
export function nextPath(path: string[], tapped: FilterChip): string[] {
  const before = path.slice(0, tapped.level - 1);
  return tapped.pressed ? before : [...before, tapped.id];
}
