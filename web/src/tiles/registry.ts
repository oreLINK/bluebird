/**
 * Tile type registry: maps the `type` of a tile in `config/tiles.yaml` to the
 * Svelte component that renders it.
 *
 * To add a tile type:
 *   1. Create `MyTile.svelte` accepting `TileProps`.
 *   2. Register it below under a new id.
 *   3. Use that id as `type` in `config/tiles.yaml`.
 */
import type { Component } from 'svelte';
import type { Kpi, Tile } from '../lib/config';
import type { MassifDaily } from '../lib/data';
import RankingTile from './RankingTile.svelte';

export interface TileProps {
  tile: Tile;
  kpis: Kpi[];
  data: MassifDaily;
}

export const TILE_COMPONENTS: Record<string, Component<TileProps>> = {
  ranking: RankingTile,
};

export function tileComponent(type: string): Component<TileProps> | undefined {
  return TILE_COMPONENTS[type];
}
