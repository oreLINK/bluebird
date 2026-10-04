import { describe, expect, it } from 'vitest';
import type { Kpi, Rewind } from './config';
import { historicalView, itemLabel, liveView, rewindOfKpi, viewFor } from './kpiView';

const name = { fr: 'x', en: 'x' };
const nbsp = (s: string) => s.replace(/[  ]/g, ' ');
const historical: Kpi = {
  id: 'snow',
  aggregator: 'a',
  name,
  description: name,
  kind: 'historical',
  value: { unit: 'm', decimals: 2, scale: 0.01 },
};
const liveKpi: Kpi = { id: 'chance', aggregator: 'a', name, description: name };
const rewind = { id: 's', name, start: '2025-12-01', end: '2026-05-01', massifs: ['m'], kpis: ['snow'], filter: 'f' } as Rewind;
const station = (id: string) => ({ id, name: `${id} long`, short_name: id });
const payload = {
  timezone: 'Europe/Paris',
  generated_at: '2026-10-04T10:00:00Z',
  stations: { a: station('a'), b: station('b') },
  sources: [],
  kpis: {
    snow: {
      kpi_id: 'snow',
      aggregator_version: '1',
      unit: 'm',
      ranking: [
        { station_id: 'a', value: 4.43, drivers: {} },
        { station_id: 'b', value: 2.215, drivers: {} },
      ],
    },
  },
} as never;

describe('kpi views', () => {
  it('ranks historical values with bars relative to the best one', () => {
    const view = historicalView(historical, rewind, 'm', payload);
    expect(view.items.map((i) => [i.stationId, i.share])).toEqual([
      ['a', 1],
      ['b', 0.5],
    ]);
    expect(view.items[0]?.confidence).toBeUndefined();
    expect(nbsp(itemLabel(view, view.items[0]!, 'fr'))).toBe('4,43 m');
  });

  it('scales bars to the KPI maximum when it has one (0-100 % for a percentage)', () => {
    const percent: Kpi = { ...historical, value: { unit: '%', decimals: 0, scale: 100, max: 100 } };
    const view = historicalView(percent, rewind, 'm', payload);
    expect(view.items.map((i) => i.share)).toEqual([0.0443, 0.02215]);
  });

  it('shows a language-dependent unit and full bars for the highest value of an ascending ranking', () => {
    const days: Kpi = {
      ...historical,
      order: 'asc',
      value: {
        unit: 'd',
        unit_label: { fr: 'jours', en: 'days' },
        unit_label_one: { fr: 'jour', en: 'day' },
        decimals: 0,
      },
    };
    const ascending = {
      ...(payload as object),
      kpis: {
        snow: {
          kpi_id: 'snow',
          aggregator_version: '1',
          unit: 'd',
          ranking: [
            { station_id: 'a', value: 5, drivers: {} },
            { station_id: 'b', value: 20, drivers: {} },
          ],
        },
      },
    } as never;
    const view = historicalView(days, rewind, 'm', ascending);
    expect(view.items.map((i) => i.share)).toEqual([0.25, 1]);
    expect(nbsp(itemLabel(view, view.items[0]!, 'fr'))).toBe('5 jours');
    expect(nbsp(itemLabel(view, view.items[0]!, 'en'))).toBe('5 days');
    const one = { ...view.items[0]!, value: 1 };
    expect(nbsp(itemLabel(view, one, 'fr'))).toBe('1 jour');
    expect(nbsp(itemLabel(view, one, 'en'))).toBe('1 day');
  });

  it('gives an empty historical view until the Rewind is built', () => {
    const view = historicalView(historical, rewind, 'm', undefined);
    expect(view.items).toEqual([]);
    expect(view.unit).toBe('m');
  });

  it('shows live probabilities as percentages with their confidence', () => {
    const period = {
      key: 'evening@2026-10-04',
      period_id: 'evening',
      ski_day: '2026-10-04',
      start: '2026-10-04T18:00:00+02:00',
      end: '2026-10-05T00:00:00+02:00',
      generated_at: '2026-10-04T04:30:00Z',
      ranking: [{ station_id: 'a', probability: 0.82, confidence: 'high' }],
    };
    const daily = {
      massif_id: 'm',
      forecast_date: '2026-10-04',
      timezone: 'Europe/Paris',
      generated_at: '2026-10-04T10:30:00Z',
      stations: {},
      sources: [],
      kpis: { chance: { periods: [period] } },
    } as never;
    const slot = {
      key: period.key,
      periodId: 'evening',
      skiDay: '2026-10-04',
      start: period.start,
      end: period.end,
    };
    const view = liveView(liveKpi, daily, slot);
    expect(view.items[0]).toMatchObject({ value: 0.82, share: 0.82, confidence: 'high' });
    expect(nbsp(itemLabel(view, view.items[0]!, 'fr'))).toBe('82 %');
    // Computed at 04:30 while the payload is from 10:30: kept from an earlier refresh.
    expect(view.stale).toBe(true);
    expect(view.generatedAt).toBe('2026-10-04T04:30:00Z');
    expect(liveView(liveKpi, daily).items).toEqual([]); // no period: no ranking
  });

  it('finds the Rewind of a KPI and waits for live data only', () => {
    expect(rewindOfKpi('snow', [rewind])).toBe(rewind);
    expect(viewFor(liveKpi, 'm', null, [rewind], () => payload)).toBeNull();
    expect(viewFor(historical, 'm', null, [rewind], () => payload)?.kind).toBe('historical');
    expect(viewFor(undefined, 'm', null, [rewind], () => payload)).toBeNull();
  });
});
