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
import pagesYaml from '@config/pages.yaml';
import rewindsYaml from '@config/rewinds.yaml';
import sourcesYaml from '@config/sources.yaml';
import tilesYaml from '@config/tiles.yaml';
import type { Filter, FiltersFile } from './generated/filters';
import type { Kpi, KpisFile } from './generated/kpis';
import type { LayoutFile } from './generated/layout';
import type { Massif, MassifsFile } from './generated/massifs';
import type { DiamondRewind } from './generated/diamond-rewind';
import type { Footer, Page, PageSection, PagesFile } from './generated/pages';
import type { Rewind, RewindsFile } from './generated/rewinds';
import type { Attribution, Source, SourcesFile } from './generated/sources';
import type { StationsFile } from './generated/stations';
import type { Tile, TilesFile } from './generated/tiles';

export type {
  Attribution,
  DiamondRewind,
  Filter,
  Footer,
  Kpi,
  Massif,
  Page,
  PageSection,
  Rewind,
  Source,
  Tile,
};

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

/** Tiles matching a level-1 filter (a KPI tagged with its id); every tile without a filter. */
export function filterTiles(resolved: ResolvedTile[], filter: Filter | undefined): ResolvedTile[] {
  if (!filter) return resolved;
  return resolved.filter(({ kpis }) => kpis.some((kpi) => kpi.filters?.includes(filter.id)));
}

/** Level-1 filters worth showing in the bar: those matching at least one tile. */
export function usableFilters(filters: Filter[], resolved: ResolvedTile[]): Filter[] {
  return filters.filter((f) => filterTiles(resolved, f).length > 0);
}

/**
 * YAML dates (`start: 2025-12-01`) reach the bundle as JavaScript `Date`
 * objects (YAML timestamps), whereas the generated types say `string`:
 * bring them back to `YYYY-MM-DD`.
 */
export function isoDate(value: string | Date): string {
  return value instanceof Date ? value.toISOString().slice(0, 10) : value;
}

/** Enabled Rewinds with their dates as `YYYY-MM-DD` strings. */
export function enabledRewinds(file: RewindsFile): Rewind[] {
  return (file.rewinds ?? [])
    .filter((r) => r.enabled !== false)
    .map((r) => ({ ...r, start: isoDate(r.start), end: isoDate(r.end) }));
}

/** Rewind payloads keyed `<rewind_id>/<massif_id>`, from `config/rewind/<id>/<massif>.json` paths. */
export function indexRewinds(files: Record<string, DiamondRewind>): Map<string, DiamondRewind> {
  const index = new Map<string, DiamondRewind>();
  for (const [path, payload] of Object.entries(files)) {
    const [rewindId, file] = path.split('/').slice(-2);
    if (rewindId && file) index.set(`${rewindId}/${file.replace(/\.json$/, '')}`, payload);
  }
  return index;
}

/** Attributions of the enabled sources, without duplicates (same name and URL), in file order. */
export function sourceAttributions(sources: Source[]): Attribution[] {
  const seen = new Set<string>();
  const result: Attribution[] = [];
  for (const source of sources) {
    if (source.enabled === false) continue;
    const key = `${source.attribution.name}|${source.attribution.url}`;
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(source.attribution);
  }
  return result;
}

/** Pages listed in the footer, in footer order; unknown ids are skipped. */
export function footerPages(file: PagesFile): Page[] {
  return file.footer.pages.flatMap((id) => file.pages.find((p) => p.id === id) ?? []);
}

const massifsFile = massifsYaml as MassifsFile;
const kpisFile = kpisYaml as KpisFile;
const tilesFile = tilesYaml as TilesFile;
const layoutFile = layoutYaml as LayoutFile;
const filtersFile = filtersYaml as FiltersFile;
const pagesFile = pagesYaml as PagesFile;
const sourcesFile = sourcesYaml as SourcesFile;
const rewindsFile = rewindsYaml as RewindsFile;

export const massifs: Massif[] = enabledMassifs(massifsFile);
export const kpis: Kpi[] = kpisFile.kpis;
export const tiles: Tile[] = tilesFile.tiles;
export const layout: LayoutFile = layoutFile;
export const filters: Filter[] = filtersFile.filters;
export const pages: Page[] = pagesFile.pages;
export const footer: Footer = pagesFile.footer;
export const footerLinks: Page[] = footerPages(pagesFile);
export const sources: Source[] = sourcesFile.sources;
export const attributions: Attribution[] = sourceAttributions(sourcesFile.sources);
export const rewinds: Rewind[] = enabledRewinds(rewindsFile);

/** Generated by `bluebird rewind` and committed; bundled at build time (no fetch). */
const rewindIndex = indexRewinds(
  import.meta.glob('@config/rewind/*/*.json', { eager: true, import: 'default' }) as Record<
    string,
    DiamondRewind
  >,
);

/** Ranked payload of a Rewind for a massif, if it was built. */
export function rewindPayload(rewindId: string, massifId: string): DiamondRewind | undefined {
  return rewindIndex.get(`${rewindId}/${massifId}`);
}

/** The Rewind shown by a level-1 filter (config/rewinds.yaml `filter`), if any. */
export function rewindOfFilter(filterId: string | undefined): Rewind | undefined {
  return rewinds.find((r) => r.filter === filterId);
}

const stationFiles = import.meta.glob('@config/stations/*.yaml', {
  eager: true,
  import: 'default',
}) as Record<string, StationsFile>;

/** Station names by `<massif_id>/<station_id>` (config/stations/<massif_id>.yaml). */
export const stationNames: Map<string, string> = new Map(
  Object.entries(stationFiles).flatMap(([path, file]) => {
    const massifId = path.split('/').at(-1)?.replace(/\.yaml$/, '') ?? '';
    return file.stations.map((s): [string, string] => [`${massifId}/${s.id}`, s.name]);
  }),
);

export function tilesForMassif(massifId: string): ResolvedTile[] {
  return resolveLayout(massifId, layout, tiles, kpis);
}
