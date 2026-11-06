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
 *   mood_group, mood  the two levels of the Mood filter (`moods`): a
 *         sub-mood (Sur place, En route) then a mood (Freerider…). The page
 *         shows every KPI of the chosen mood(s), ordered by the visibility
 *         score (`moodFeed` of lib/homeFeed.ts); no day or slot level.
 * Grain rule: until a slot is chosen, the page only shows day-grain tiles
 * (periods with `native_window`: today, tonight…) and Rewind tiles; the time
 * slot tiles appear at the slot level only, so the page stays short.
 * The bar shows the chosen chips (pressed, removable), then the options of the
 * next level, only those that still have tiles. With nothing chosen it shows
 * every level-1 filter and the page shows the home feed (lib/homeFeed.ts):
 * the pinned tiles of config/layout.yaml `home`, then the tiles ranked by
 * their visibility score (never shown), at most `limit` tiles.
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
import { type HomeOptions, homeFeed, moodFeed } from './homeFeed';
import {
  type Period,
  type TileInstance,
  daysBetween,
  expandTiles,
  isLiveTile,
  periodsFile,
  referenceDay,
} from './periods';

export type LevelKind = NonNullable<Filter['levels']>[number];
/** The levels of the Mood filter, handled by `moodState` (not LEVEL_KINDS). */
export type MoodLevelKind = 'mood_group' | 'mood';

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

export const LEVEL_KINDS: Record<Exclude<LevelKind, MoodLevelKind>, LevelKindSpec> = {
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

/** What the filter bar and the page show for a selection path. */
export function filterState(
  path: string[],
  filters: Filter[],
  resolved: ResolvedTile[],
  payload: MassifDaily | null,
  now: number,
  home: HomeOptions = {},
  periods: Period[] = periodsFile.periods,
  days: Localized[] = periodsFile.days ?? [],
): FilterState {
  const bar = usableFilters(filters, resolved);
  const topic = bar.find((f) => f.id === path[0]);

  if (!topic) {
    const chips = bar.map((f) => chip(f, false));
    return { path: [], chips, ...homeFeed(resolved, payload, now, home, periods) };
  }

  if (topic.moods?.length) return moodState(path, topic, resolved, payload, now, home, periods);

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
  for (const kind of (topic.levels ?? []) as Exclude<LevelKind, MoodLevelKind>[]) {
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

/**
 * The Mood filter: level 2 = its sub-moods, level 3 = the moods of the chosen
 * one (only those with a tile). The page shows the KPIs of the chosen mood, or
 * of every mood above it, through `moodFeed` (a `tomorrow_only` sub-mood keeps
 * tomorrow alone).
 */
function moodState(
  path: string[],
  topic: Filter,
  resolved: ResolvedTile[],
  payload: MassifDaily | null,
  now: number,
  home: HomeOptions,
  periods: Period[],
): FilterState {
  const hasTile = (kpis: string[]) =>
    resolved.some((r) => isLiveTile(r) && kpis.includes(r.kpis[0]?.id ?? ''));
  const groups = (topic.moods ?? [])
    .map((g) => ({ ...g, moods: g.moods.filter((m) => hasTile(m.kpis)) }))
    .filter((g) => g.moods.length > 0);
  const levelChip = (level: number, option: LevelOption & { icon?: string | null }, pressed: boolean) => ({
    key: `${level}:${option.id}`,
    id: option.id,
    name: option.name,
    icon: option.icon ?? null,
    level,
    pressed,
  });
  const kept = [topic.id];
  const chips: FilterChip[] = [chip(topic, true)];
  const group = groups.find((g) => g.id === path[1]);
  const mood = group?.moods.find((m) => m.id === path[2]);
  if (!group) chips.push(...groups.map((g) => levelChip(2, g, false)));
  else {
    kept.push(group.id);
    chips.push(levelChip(2, group, true));
    if (!mood) chips.push(...group.moods.map((m) => levelChip(3, m, false)));
    else {
      kept.push(mood.id);
      chips.push(levelChip(3, mood, true));
    }
  }
  const moods = mood ? [mood] : group ? group.moods : groups.flatMap((g) => g.moods);
  const kpis = [...new Set(moods.flatMap((m) => m.kpis))];
  const feed = moodFeed(resolved, payload, now, {
    ...home,
    kpis,
    tomorrowOnly: group?.tomorrow_only ?? false,
  }, periods);
  return { path: kept, chips, ...feed };
}

/** A day-grain tile (period with `native_window`) or a Rewind tile (no period). */
export function isDayGrain(instance: TileInstance, periods: Period[] = periodsFile.periods): boolean {
  if (!instance.slot) return true;
  return periods.find((p) => p.id === instance.slot?.periodId)?.native_window === true;
}

/** Deepest filter path remembered: the topic plus three levels (`MAX_FILTER_LEVELS` of config.py). */
export const MAX_FILTER_LEVELS = 4;

/**
 * The filter path stored in `localStorage` (`filter`): `snow`, or every level
 * joined with `/` (`mood/on-site/freerider`). Values saved before the whole
 * path was kept are a level-1 id, read the same way. Unknown or stale items
 * (a slot already over) are dropped by `filterState`.
 */
export function readFilterPath(value: string | null): string[] {
  return (value ?? '').split('/').filter(Boolean).slice(0, MAX_FILTER_LEVELS);
}

/** The value stored for a filter path. */
export function writeFilterPath(path: string[]): string {
  return path.slice(0, MAX_FILTER_LEVELS).join('/');
}

/**
 * The path after a tap on a chip: a pressed chip is removed with the levels
 * after it; another chip is chosen at its level.
 */
export function nextPath(path: string[], tapped: FilterChip): string[] {
  const before = path.slice(0, tapped.level - 1);
  return tapped.pressed ? before : [...before, tapped.id];
}
