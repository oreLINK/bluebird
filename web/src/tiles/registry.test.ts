import { describe, expect, it } from 'vitest';
import { kpis, tiles } from '../lib/config';
import { TILE_COMPONENTS } from './registry';
import { booleanOption, numberOption } from './options';

describe('tile registry', () => {
  it('has a component for every tile type used in config/tiles.yaml', () => {
    for (const tile of tiles) expect(TILE_COMPONENTS, tile.id).toHaveProperty(tile.type);
  });

  it('only references existing KPIs', () => {
    const kpiIds = new Set(kpis.map((k) => k.id));
    for (const tile of tiles) for (const id of tile.kpis ?? []) expect(kpiIds.has(id), id).toBe(true);
  });

  it('reads typed options with fallbacks', () => {
    expect(numberOption({ visible_rows: 3 }, 'visible_rows', 5)).toBe(3);
    expect(numberOption({ visible_rows: 'x' }, 'visible_rows', 5)).toBe(5);
    expect(booleanOption(undefined, 'show_odds', false)).toBe(false);
  });
});
