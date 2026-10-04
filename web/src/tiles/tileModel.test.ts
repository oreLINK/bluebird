import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { filters, kpis, rewindPayload, rewinds } from '../lib/config';
import type { MassifDaily } from '../lib/data';
import { liveView, viewFor } from '../lib/kpiView';
import { payloadSlots } from '../lib/periods';
import { tileModel, tileTheme } from './tileModel';

const demo = JSON.parse(
  readFileSync(new URL('../../public/data/diamond/pyrenees/latest.json', import.meta.url), 'utf8'),
) as MassifDaily;

const live = kpis.find((k) => k.id === 'offpiste_powder_chance')!;
const historical = kpis.find((k) => k.id === 'season_total_snowfall')!;
const tile = { id: 't', type: 'banner', kpis: ['x'] };
/** The first period of the KPI in the demo payload. */
const slot = payloadSlots(demo, 0).find((s) => s.key === demo.kpis[live.id]!.periods[0]!.key)!;

describe('tileModel', () => {
  it('keeps station details off unless a live tile enables them', () => {
    const view = liveView(live, demo, slot);
    expect(tileModel(tile, view).details).toBe(false);
    expect(tileModel({ ...tile, options: { details: true } }, view).details).toBe(true);
  });

  it('flags live values kept from an earlier refresh', () => {
    const fresh = tileModel(tile, liveView(live, demo, slot));
    expect(fresh.staleSince).toBeNull();
    const older = structuredClone(demo);
    older.kpis[live.id]!.periods[0]!.generated_at = '2027-01-14T23:07:00Z';
    expect(tileModel(tile, liveView(live, older, slot)).staleSince).toBe('2027-01-14T23:07:00Z');
  });

  it('splits the ranking into the top stations and the rest', () => {
    const model = tileModel({ ...tile, options: { top: 2 } }, liveView(live, demo, slot));
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
    const view = liveView(live, demo, slot);
    expect(tileTheme({ options: { theme: 'rewind' } }, view, filters)).toBe('rewind');
    expect(tileTheme({ options: { theme: 'nope' } }, view, filters)).toBe('default');
  });
});
