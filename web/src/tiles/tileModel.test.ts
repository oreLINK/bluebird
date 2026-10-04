import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { filters, kpis, rewindPayload, rewinds } from '../lib/config';
import type { MassifDaily } from '../lib/data';
import { liveView, viewFor } from '../lib/kpiView';
import { tileModel, tileTheme } from './tileModel';

const demo = JSON.parse(
  readFileSync(new URL('../../public/data/diamond/pyrenees/latest.json', import.meta.url), 'utf8'),
) as MassifDaily;

const live = kpis.find((k) => k.id === 'offpiste_powder_chance')!;
const historical = kpis.find((k) => k.id === 'season_total_snowfall')!;
const tile = { id: 't', type: 'banner', kpis: ['x'] };

describe('tileModel', () => {
  it('keeps station details off unless a live tile enables them', () => {
    const view = liveView(live, demo);
    expect(tileModel(tile, view).details).toBe(false);
    expect(tileModel({ ...tile, options: { details: true } }, view).details).toBe(true);
  });

  it('splits the ranking into the top stations and the rest', () => {
    const model = tileModel({ ...tile, options: { top: 2 } }, liveView(live, demo));
    expect(model.top).toHaveLength(2);
    expect(model.top.length + model.rest.length).toBe(model.items.length);
  });

  it('dresses historical tiles in their Rewind theme with a badge, without odds or details', () => {
    const view = viewFor(historical, 'pyrenees', null, rewinds, rewindPayload);
    expect(view?.kind).toBe('historical');
    const model = tileModel({ ...tile, options: { show_odds: true, details: true } }, view!);
    expect(model.theme).toBe('rewind');
    expect(model.badge?.fr).toBe('Rewind 25/26');
    expect(model.showOdds).toBe(false);
    expect(model.details).toBe(false);
    expect(model.emptyMessage).toBe('rewind.noData');
  });

  it('lets the tile option override the theme', () => {
    const view = liveView(live, demo);
    expect(tileTheme({ options: { theme: 'rewind' } }, view, filters)).toBe('rewind');
    expect(tileTheme({ options: { theme: 'nope' } }, view, filters)).toBe('default');
  });
});
