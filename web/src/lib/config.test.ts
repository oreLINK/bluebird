import { describe, expect, it } from 'vitest';
import {
  enabledMassifs,
  filterTiles,
  filters,
  footer,
  footerLinks,
  footerPages,
  enabledRewinds,
  indexRewinds,
  kpis,
  layout,
  massifs,
  pages,
  resolveLayout,
  rewindOfFilter,
  rewinds,
  sourceAttributions,
  stationNames,
  tiles,
  usableFilters,
} from './config';
import type { Kpi } from './generated/kpis';
import type { Massif } from './generated/massifs';
import type { Tile } from './generated/tiles';

const name = { fr: 'x', en: 'x' };
const kpi = (id: string, enabled = true): Kpi => ({ id, aggregator: id, enabled, name, description: name });
const tile = (id: string, kpiIds: string[]): Tile => ({ id, type: 'ranking', kpis: kpiIds });

describe('resolveLayout', () => {
  const allTiles = [tile('a', ['k1']), tile('b', ['k2']), tile('c', ['k3'])];
  const allKpis = [kpi('k1'), kpi('k2'), kpi('k3', false)];

  it('follows the default order and skips unknown tiles', () => {
    const result = resolveLayout('pyrenees', { default: ['b', 'missing', 'a'] }, allTiles, allKpis);
    expect(result.map((r) => r.tile.id)).toEqual(['b', 'a']);
    expect(result[0]?.kpis.map((k) => k.id)).toEqual(['k2']);
  });

  it('uses the massif override when present', () => {
    const result = resolveLayout(
      'alps',
      { default: ['a', 'b'], overrides: { alps: ['b'] } },
      allTiles,
      allKpis,
    );
    expect(result.map((r) => r.tile.id)).toEqual(['b']);
  });

  it('drops tiles whose KPIs are all disabled', () => {
    const result = resolveLayout('pyrenees', { default: ['a', 'c'] }, allTiles, allKpis);
    expect(result.map((r) => r.tile.id)).toEqual(['a']);
  });
});

describe('enabledMassifs', () => {
  it('filters disabled massifs and sorts by order then id', () => {
    const m = (id: string, order: number, enabled = true): Massif => ({
      id,
      name,
      bbox: [0, 0, 1, 1],
      order,
      enabled,
    });
    const result = enabledMassifs({ massifs: [m('b', 20), m('a', 20), m('c', 10), m('d', 1, false)] });
    expect(result.map((x) => x.id)).toEqual(['c', 'a', 'b']);
  });
});

describe('repository configuration', () => {
  it('bundles at least one massif and a resolvable layout', () => {
    expect(massifs.length).toBeGreaterThan(0);
    const resolved = resolveLayout(massifs[0]!.id, layout, tiles, kpis);
    expect(resolved.length).toBe(layout.default.length);
  });
});

describe('filters', () => {
  const name = { fr: 'x', en: 'x' };
  const snowKpi: Kpi = { id: 'k1', aggregator: 'a', name, description: name, filters: ['snow'] };
  const powderKpi: Kpi = { id: 'k2', aggregator: 'a', name, description: name, filters: ['powder'] };
  const resolved = [
    { tile: { id: 't1', type: 'banner', kpis: ['k1'] }, kpis: [snowKpi] },
    { tile: { id: 't2', type: 'banner', kpis: ['k2'] }, kpis: [powderKpi] },
  ];
  const all = { id: 'all', name, all: true };
  const snow = { id: 'snow', name };
  const wind = { id: 'wind', name };

  it('keeps every tile for an all filter and tagged tiles otherwise', () => {
    expect(filterTiles(resolved, all).map((r) => r.tile.id)).toEqual(['t1', 't2']);
    expect(filterTiles(resolved, snow).map((r) => r.tile.id)).toEqual(['t1']);
    expect(filterTiles(resolved, undefined)).toHaveLength(2);
  });

  it('keeps the tiles of exclusive filters out of the all filter', () => {
    const rewindKpi: Kpi = { id: 'k3', aggregator: 'a', name, description: name, filters: ['rewind'] };
    const withRewind = [...resolved, { tile: { id: 't3', type: 'rewind', kpis: ['k3'] }, kpis: [rewindKpi] }];
    const rewind = { id: 'rewind', name, exclusive: true };
    const bar = [all, rewind, snow];
    expect(filterTiles(withRewind, all, bar).map((r) => r.tile.id)).toEqual(['t1', 't2']);
    expect(filterTiles(withRewind, rewind, bar).map((r) => r.tile.id)).toEqual(['t3']);
    expect(usableFilters(bar, withRewind).map((f) => f.id)).toEqual(['all', 'rewind', 'snow']);
  });

  it('hides filters that match no tile of the current layout', () => {
    expect(usableFilters([all, snow, wind], resolved).map((f) => f.id)).toEqual(['all', 'snow']);
  });

  it('bundles the repository filters with at least one usable filter', () => {
    expect(usableFilters(filters, resolveLayout(massifs[0]!.id, layout, tiles, kpis)).length).toBeGreaterThan(1);
  });
});

describe('pages and footer', () => {
  const title = { fr: 'x', en: 'x' };
  const page = (id: string) => ({ id, title, sections: [{ id: 's', title, paragraphs: [title] }] });

  it('lists footer pages in footer order and skips unknown ids', () => {
    const file = {
      footer: { repository: 'https://example.org', pages: ['b', 'missing', 'a'] },
      pages: [page('a'), page('b')],
    };
    expect(footerPages(file as never).map((p) => p.id)).toEqual(['b', 'a']);
  });

  it('lists the attribution of enabled sources once', () => {
    const attribution = { name: 'Open-Meteo', url: 'https://open-meteo.com/', license: 'CC BY 4.0' };
    const source = (id: string, enabled = true) => ({ id, extractor: id, transformer: id, enabled, attribution });
    const other = { ...source('c'), attribution: { name: 'OSM', url: 'https://osm.org' } };
    expect(sourceAttributions([source('a'), source('b'), source('x', false), other])).toEqual([
      attribution,
      other.attribution,
    ]);
  });

  it('bundles a footer with a repository link and existing pages', () => {
    expect(footer.repository).toMatch(/^https:\/\/github\.com\//);
    expect(footerLinks.length).toBe(footer.pages.length);
    expect(pages.map((p) => p.id)).toEqual(expect.arrayContaining(['legal', 'privacy']));
  });

  it('knows station names by massif and id', () => {
    expect(stationNames.get('pyrenees/cauterets')).toMatch(/Cauterets/);
  });
});

describe('rewinds', () => {
  it('indexes Rewind payloads by rewind and massif from their file paths', () => {
    const payload = { rewind_id: '2025-26', massif_id: 'pyrenees' } as never;
    const index = indexRewinds({ '/config/rewind/2025-26/pyrenees.json': payload });
    expect(index.get('2025-26/pyrenees')).toBe(payload);
  });

  it('turns YAML dates (parsed as Date objects) back into YYYY-MM-DD strings', () => {
    const rewind = { id: 'x', name, start: new Date('2025-12-01') as never, end: '2026-05-01', massifs: ['m'] as [string], kpis: ['k'] as [string], filter: 'f' };
    expect(enabledRewinds({ rewinds: [rewind, { ...rewind, id: 'off', enabled: false }] })).toEqual([
      { ...rewind, start: '2025-12-01' },
    ]);
  });

  it('bundles the Rewind 25/26 with string dates', () => {
    const rewind = rewinds.find((r) => r.id === '2025-26');
    expect(rewind?.start).toBe('2025-12-01');
    expect(rewind?.end).toBe('2026-05-01');
  });

  it('bundles the Rewind 25/26 behind an exclusive filter placed right after "All"', () => {
    const rewind = rewinds.find((r) => r.id === '2025-26');
    expect(rewind).toBeDefined();
    expect(rewindOfFilter(rewind!.filter)).toBe(rewind);
    const index = filters.findIndex((f) => f.id === rewind!.filter);
    expect(filters[index - 1]?.all).toBe(true);
    expect(filters[index]?.exclusive).toBe(true);
  });
});
