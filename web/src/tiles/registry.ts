/**
 * Tile type registry: maps the `type` of a tile in `config/tiles.yaml` to the
 * Svelte component that renders it.
 *
 * Naming convention: a tile type id in snake_case is rendered by `Tile` + its
 * PascalCase form: `banner` → `TileBanner.svelte`, `banner_full` →
 * `TileBannerFull.svelte` (checked by a test).
 *
 * To add a tile type:
 *   1. Create `TileXyz.svelte` accepting `TileProps` (wrap it in the shared
 *      `card` frame, or in `TileShell` for a list-style tile).
 *   2. Register it below under the id `xyz`.
 *   3. Use `type: xyz` in `config/tiles.yaml`.
 */
import type { Component } from 'svelte';
import type { Kpi, Tile } from '../lib/config';
import type { MassifDaily } from '../lib/data';
import TileBanner from './TileBanner.svelte';
import TileBannerFull from './TileBannerFull.svelte';
import TileRanking from './TileRanking.svelte';

export interface TileProps {
  tile: Tile;
  kpis: Kpi[];
  data: MassifDaily;
}

export const TILE_COMPONENTS: Record<string, Component<TileProps>> = {
  banner: TileBanner,
  banner_full: TileBannerFull,
  ranking: TileRanking,
};

export function tileComponent(type: string): Component<TileProps> | undefined {
  return TILE_COMPONENTS[type];
}
