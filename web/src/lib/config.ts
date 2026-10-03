/**
 * Site configuration, bundled at build time from the repository `config/` YAML.
 *
 * The pipeline validates these files (`bluebird validate`) and exports their
 * JSON Schemas, from which `src/lib/generated/*` types are produced. Pure
 * helpers take their inputs as arguments so they can be unit-tested.
 */
import filtersYaml from '@config/filters.yaml';
import kpisYaml from '@config/kpis.yaml';
import layoutYaml from '@config/layout.yaml';
import massifsYaml from '@config/massifs.yaml';
import tilesYaml from '@config/tiles.yaml';
import type { Filter, FiltersFile } from './generated/filters';
import type { Kpi, KpisFile } from './generated/kpis';
import type { LayoutFile } from './generated/layout';
import type { Massif, MassifsFile } from './generated/massifs';
import type { Tile, TilesFile } from './generated/tiles';

export type { Filter, Kpi, Massif, Tile };

/** Enabled massifs, sorted by `order` then id. */
export function enabledMassifs(file: MassifsFile): Massif[] {
  return file.massifs
    .filter((m) => m.enabled !== false)
    .sort((a, b) => (a.order ?? 100) - (b.order ?? 100) || a.id.localeCompare(b.id));
}

/** A tile resolved with its KPI definitions. */
export interface ResolvedTile {
  tile: Tile;
  kpis: Kpi[];
}

/**
 * Tiles to show for a massif, in layout order. Unknown tile ids and tiles
 * whose KPIs are all disabled are dropped.
 */
export function resolveLayout(
  massifId: string,
  layout: LayoutFile,
  tiles: Tile[],
  kpis: Kpi[],
): ResolvedTile[] {
  const tilesById = new Map(tiles.map((t) => [t.id, t]));
  const kpisById = new Map(kpis.filter((k) => k.enabled !== false).map((k) => [k.id, k]));
  const order = layout.overrides?.[massifId] ?? layout.default;
  const resolved: ResolvedTile[] = [];
  for (const tileId of order) {
    const tile = tilesById.get(tileId);
    if (!tile) continue;
    const tileKpis = (tile.kpis ?? []).flatMap((id) => kpisById.get(id) ?? []);
    if ((tile.kpis ?? []).length > 0 && tileKpis.length === 0) continue;
    resolved.push({ tile, kpis: tileKpis });
  }
  return resolved;
}

/** Tiles matching a filter: every tile for an `all` filter, else tiles with a tagged KPI. */
export function filterTiles(resolved: ResolvedTile[], filter: Filter | undefined): ResolvedTile[] {
  if (!filter || filter.all) return resolved;
  return resolved.filter(({ kpis }) => kpis.some((kpi) => kpi.filters?.includes(filter.id)));
}

/** Filters worth showing in the bar: `all` ones, and those matching at least one tile. */
export function usableFilters(filters: Filter[], resolved: ResolvedTile[]): Filter[] {
  return filters.filter((f) => f.all || filterTiles(resolved, f).length > 0);
}

const massifsFile = massifsYaml as MassifsFile;
const kpisFile = kpisYaml as KpisFile;
const tilesFile = tilesYaml as TilesFile;
const layoutFile = layoutYaml as LayoutFile;
const filtersFile = filtersYaml as FiltersFile;

export const massifs: Massif[] = enabledMassifs(massifsFile);
export const kpis: Kpi[] = kpisFile.kpis;
export const tiles: Tile[] = tilesFile.tiles;
export const layout: LayoutFile = layoutFile;
export const filters: Filter[] = filtersFile.filters;

export function tilesForMassif(massifId: string): ResolvedTile[] {
  return resolveLayout(massifId, layout, tiles, kpis);
}
