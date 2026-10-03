/**
 * Site configuration, bundled at build time from the repository `config/` YAML.
 *
 * The pipeline validates these files (`bluebird validate`) and exports their
 * JSON Schemas, from which `src/lib/generated/*` types are produced. Pure
 * helpers take their inputs as arguments so they can be unit-tested.
 */
import kpisYaml from '@config/kpis.yaml';
import layoutYaml from '@config/layout.yaml';
import massifsYaml from '@config/massifs.yaml';
import tilesYaml from '@config/tiles.yaml';
import type { Kpi, KpisFile } from './generated/kpis';
import type { LayoutFile } from './generated/layout';
import type { Massif, MassifsFile } from './generated/massifs';
import type { Tile, TilesFile } from './generated/tiles';

export type { Kpi, Massif, Tile };

/** KPI whose best probability drives the intensity of the falling-snow ambience. */
export const AMBIENT_SNOW_KPI = 'snowfall_chance';

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

const massifsFile = massifsYaml as MassifsFile;
const kpisFile = kpisYaml as KpisFile;
const tilesFile = tilesYaml as TilesFile;
const layoutFile = layoutYaml as LayoutFile;

export const massifs: Massif[] = enabledMassifs(massifsFile);
export const kpis: Kpi[] = kpisFile.kpis;
export const tiles: Tile[] = tilesFile.tiles;
export const layout: LayoutFile = layoutFile;

export function tilesForMassif(massifId: string): ResolvedTile[] {
  return resolveLayout(massifId, layout, tiles, kpis);
}
