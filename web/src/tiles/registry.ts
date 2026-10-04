/**
 * Tile type registry: maps the `type` of a tile in `config/tiles.yaml` to the
 * Svelte component that renders it.
 *
 * Naming convention: a tile type id in snake_case is rendered by `Tile` + its
 * PascalCase form: `banner` → `TileBanner.svelte`, `banner_full` →
 * `TileBannerFull.svelte` (checked by a test).
 *
 * Every tile type renders any KPI, live or historical: it receives a KpiView
 * (lib/kpiView.ts) built by App.svelte, and its look comes from TileModel
 * (tileModel.ts), including the colour theme (e.g. Rewind red).
 *
 * To add a tile type:
 *   1. Create `TileXyz.svelte` accepting `TileProps` (wrap it in the shared
 *      `card` frame, or in `TileShell` for a list-style tile).
 *   2. Register it below under the id `xyz`.
 *   3. Map it to a loading placeholder in `skeletonVariant` below.
 *   4. Use `type: xyz` in `config/tiles.yaml`.
 */
import type { Component } from 'svelte';
import type { Kpi, Tile } from '../lib/config';
import type { KpiView } from '../lib/kpiView';
import TileBanner from './TileBanner.svelte';
import TileBannerFull from './TileBannerFull.svelte';
import TileRanking from './TileRanking.svelte';
import TileSimple from './TileSimple.svelte';

export interface TileProps {
  tile: Tile;
  kpis: Kpi[];
  /** The tile's first KPI, with its ranking (live or historical). */
  view: KpiView;
}

export const TILE_COMPONENTS: Record<string, Component<TileProps>> = {
  banner: TileBanner,
  banner_full: TileBannerFull,
  ranking: TileRanking,
  simple: TileSimple,
};

export function tileComponent(type: string): Component<TileProps> | undefined {
  return TILE_COMPONENTS[type];
}

/** Layout of the placeholder (TileSkeleton) shown while a tile of this type loads. */
export type SkeletonVariant = 'banner' | 'full' | 'simple' | 'list';

const SKELETON_VARIANTS: Record<string, SkeletonVariant> = {
  banner: 'banner',
  banner_full: 'full',
  simple: 'simple',
};

export function skeletonVariant(type: string): SkeletonVariant {
  return SKELETON_VARIANTS[type] ?? 'list';
}
