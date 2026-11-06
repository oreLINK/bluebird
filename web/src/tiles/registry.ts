/**
 * Tile format registry: maps the `format` of a tile in `config/tiles.yaml` to
 * the Svelte component that renders it (the other axes, `scope` and `visual`,
 * are read by the components themselves).
 *
 * Naming convention: a format id in snake_case is rendered by `Tile` + its
 * PascalCase form: `full` → `TileFull.svelte`, `compact` →
 * `TileCompact.svelte` (checked by a test).
 *
 * Every format renders any KPI, live or historical: it receives a KpiView
 * (lib/kpiView.ts) built by App.svelte, and its look comes from TileModel
 * (tileModel.ts), including the colour theme (e.g. Rewind red).
 *
 * To add a tile format:
 *   1. Create `TileXyz.svelte` accepting `TileProps`, wrapped in a `FlipCard`
 *      with the shared `card` frame on each face.
 *   2. Register it below under the id `xyz`.
 *   3. Map it to a loading placeholder in `skeletonVariant` below.
 *   4. Add `xyz` to `TileFormat` (pipeline config.py), run `bluebird schemas`
 *      and `npm run gen:types`, then use `format: xyz` in `config/tiles.yaml`.
 */
import type { Component } from 'svelte';
import type { Kpi, Tile } from '../lib/config';
import type { KpiView } from '../lib/kpiView';
import type { LiveWebcam } from '../lib/webcams';
import TileBanner from './TileBanner.svelte';
import TileCompact from './TileCompact.svelte';
import TileFull from './TileFull.svelte';

export interface TileProps {
  tile: Tile;
  kpis: Kpi[];
  /** The tile's first KPI, with its ranking (live or historical). */
  view: KpiView;
  /** Live webcam link of the leading station, when the tile's `webcam` rule holds. */
  webcam?: LiveWebcam | null;
}

export const TILE_COMPONENTS: Record<string, Component<TileProps>> = {
  full: TileFull,
  banner: TileBanner,
  compact: TileCompact,
};

export function tileComponent(format: string): Component<TileProps> | undefined {
  return TILE_COMPONENTS[format];
}

/** Layout of the placeholder (TileSkeleton) shown while a tile of this type loads. */
export type SkeletonVariant = 'banner' | 'full' | 'compact';

const SKELETON_VARIANTS: Record<string, SkeletonVariant> = {
  full: 'full',
  banner: 'banner',
  compact: 'compact',
};

export function skeletonVariant(format: string): SkeletonVariant {
  return SKELETON_VARIANTS[format] ?? 'compact';
}

/**
 * Grid rows a tile of this format spans on wide screens (App.svelte): `full`
 * and `banner` tiles are as tall as two compact tiles and the gap between them
 * (`--tile-compact-h` in styles/base.css), so two compact tiles stack beside one.
 */
export function tileRows(format: string): 1 | 2 {
  return format === 'banner' || format === 'full' ? 2 : 1;
}
