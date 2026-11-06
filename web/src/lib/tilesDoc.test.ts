/**
 * TILES.md (repository root) documents the tile axes and lists every tile:
 * these checks fail when it no longer matches config/tiles.yaml, so the file
 * is updated with every tile change (AGENTS.md §1).
 */
import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { TILE_COMPONENTS } from '../tiles/registry';
import { kpis, layout, tiles } from './config';

const ROOT = new URL('../../../', import.meta.url);
const doc = readFileSync(new URL('TILES.md', ROOT), 'utf8');

const kindOf = (kpiId: string | undefined) => kpis.find((k) => k.id === kpiId)?.kind ?? 'live';
const percent = (p: number) => `${Math.round(p * 100)} %`;

/** The inventory row a tile should have in TILES.md §7. */
function row(tile: (typeof tiles)[number]): string {
  const kpi = tile.kpis?.[0];
  const visual = tile.format === 'compact' ? '—' : (tile.visual ?? 'scene');
  const webcam = tile.webcam
    ? `${tile.webcam.positions.join(', ')} ≥ ${percent(tile.webcam.min_probability ?? 0.6)}`
    : '—';
  return `| \`${tile.id}\` | \`${kpi}\` | ${tile.scope ?? 'ranking'} | ${tile.format} | ${visual} | ${kindOf(kpi)} | ${webcam} |`;
}

describe('TILES.md', () => {
  it('lists every tile with its axes, in layout order', () => {
    const order = layout.default.filter((id) => tiles.some((t) => t.id === id));
    const unlisted = tiles.filter((t) => !order.includes(t.id)).map((t) => t.id);
    const expected = [...order, ...unlisted].map((id) => row(tiles.find((t) => t.id === id)!));
    const actual = doc.split('\n').filter((line) => /^\| `[a-z0-9_]+` \| `/.test(line));
    expect(actual).toEqual(expected);
  });

  it('states the right totals', () => {
    const count = (format: string) => tiles.filter((t) => t.format === format).length;
    const historical = tiles.filter((t) => kindOf(t.kpis?.[0]) === 'historical').length;
    const totals =
      `Totals: ${tiles.length} tiles — ${count('full')} \`full\`, ${count('banner')} \`banner\`, ` +
      `${count('compact')} \`compact\`; ${tiles.length - historical} live, ${historical} historical; ` +
      `${tiles.filter((t) => t.webcam).length} with a webcam rule.`;
    expect(doc.replace(/\s+/g, ' ')).toContain(totals);
  });

  it('describes every format of the registry', () => {
    for (const format of Object.keys(TILE_COMPONENTS)) expect(doc, format).toContain(`**\`${format}\`**`);
  });

  it('only shows pictures that exist', () => {
    const pictures = [...doc.matchAll(/src="(docs\/tiles\/[^"]+\.svg)"/g)].map((m) => m[1]!);
    expect(pictures.length).toBeGreaterThan(0);
    for (const path of pictures) expect(existsSync(new URL(path, ROOT)), path).toBe(true);
  });
});
