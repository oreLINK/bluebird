import { describe, expect, it } from 'vitest';
import { kpis, tiles } from '../lib/config';
import { TILE_COMPONENTS, skeletonVariant, tileRows } from './registry';
import { bannerScene, booleanOption, numberOption } from './options';

describe('tile registry', () => {
  it('has a component for every tile format used in config/tiles.yaml', () => {
    for (const tile of tiles) expect(TILE_COMPONENTS, tile.id).toHaveProperty(tile.format);
  });

  it('has exactly the three formats full, banner and compact', () => {
    expect(Object.keys(TILE_COMPONENTS).sort()).toEqual(['banner', 'compact', 'full']);
  });

  it('only references existing KPIs', () => {
    const kpiIds = new Set(kpis.map((k) => k.id));
    for (const tile of tiles) for (const id of tile.kpis ?? []) expect(kpiIds.has(id), id).toBe(true);
  });

  it('reads typed options with fallbacks', () => {
    expect(numberOption({ top: 2 }, 'top', 3)).toBe(2);
    expect(numberOption({ top: 'x' }, 'top', 3)).toBe(3);
    expect(booleanOption(undefined, 'show_odds', false)).toBe(false);
  });

  it('picks the banner scene from options, then from the icon', () => {
    expect(bannerScene({ options: { scene: 'piste' }, icon: 'snowflake' })).toBe('piste');
    expect(bannerScene({ options: { scene: 'nope' }, icon: 'snowflake' })).toBe('snowfall');
    expect(bannerScene({ icon: 'mountain' })).toBe('offpiste');
    expect(bannerScene({})).toBe('mountain');
  });

  it('shows a placeholder shaped like each tile format', () => {
    expect(skeletonVariant('banner')).toBe('banner');
    expect(skeletonVariant('full')).toBe('full');
    expect(skeletonVariant('compact')).toBe('compact');
    expect(skeletonVariant('unknown')).toBe('compact');
  });

  it('follows the Tile + PascalCase(type) naming convention', () => {
    const pascal = (id: string) =>
      id
        .split('_')
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join('');
    for (const [type, component] of Object.entries(TILE_COMPONENTS)) {
      expect(component.name, type).toBe(`Tile${pascal(type)}`);
    }
  });

  it('makes full and banner tiles span two grid rows and compact tiles one', () => {
    expect(tileRows('banner')).toBe(2);
    expect(tileRows('full')).toBe(2);
    expect(tileRows('compact')).toBe(1);
  });
});
