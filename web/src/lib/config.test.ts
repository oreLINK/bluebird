import { describe, expect, it } from 'vitest';
import {
  enabledMassifs,
  filterTiles,
  filters,
  kpis,
  layout,
  massifs,
  resolveLayout,
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

  it('hides filters that match no tile of the current layout', () => {
    expect(usableFilters([all, snow, wind], resolved).map((f) => f.id)).toEqual(['all', 'snow']);
  });

  it('bundles the repository filters with at least one usable filter', () => {
    expect(usableFilters(filters, resolveLayout(massifs[0]!.id, layout, tiles, kpis)).length).toBeGreaterThan(1);
  });
});
