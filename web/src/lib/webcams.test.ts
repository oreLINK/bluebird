import { describe, expect, it } from 'vitest';
import { type Tile, type Webcam, stationWebcams, tiles } from './config';
import type { KpiView } from './kpiView';
import { liveWebcam } from './webcams';

type Position = Webcam['position'];

const cam = (id: string, position: Position): Webcam => ({
  id,
  name: id,
  position,
  provider: 'skaping',
  url: `https://www.skaping.com/test/${id}`,
});
const webcams = new Map([['pyrenees/alpha', [cam('village', 'village'), cam('top', 'summit')]]]);
const start = Date.parse('2026-12-14T05:00:00Z');
const end = Date.parse('2026-12-14T17:00:00Z');
const noon = Date.parse('2026-12-14T11:00:00Z');

/** A tile `webcam` rule (at least one position). */
const ruleOf = (positions: [Position, ...Position[]], min?: number): Pick<Tile, 'webcam'> => ({
  webcam: min === undefined ? { positions } : { positions, min_probability: min },
});
const rule = ruleOf(['summit'], 0.6);

const view = (stationId: string, probability: number, kind = 'live'): KpiView =>
  ({
    kind,
    massifId: 'pyrenees',
    slot: {
      key: 'day@2026-12-14',
      periodId: 'day',
      skiDay: '2026-12-14',
      start: new Date(start).toISOString(),
      end: new Date(end).toISOString(),
    },
    items: [{ stationId, value: probability, share: probability }],
  }) as unknown as KpiView;

describe('liveWebcam', () => {
  it('links the webcam of the leading station while the period is in progress', () => {
    expect(liveWebcam(rule, view('alpha', 0.8), noon, webcams)).toEqual({
      stationId: 'alpha',
      webcam: cam('top', 'summit'),
    });
  });

  it('only links during the period: never before it starts (tomorrow) or once it is over', () => {
    expect(liveWebcam(rule, view('alpha', 0.8), start - 1, webcams)).toBeNull();
    expect(liveWebcam(rule, view('alpha', 0.8), start, webcams)).not.toBeNull();
    expect(liveWebcam(rule, view('alpha', 0.8), end, webcams)).toBeNull();
  });

  it('needs the minimum probability (0.6 by default)', () => {
    expect(liveWebcam(rule, view('alpha', 0.59), noon, webcams)).toBeNull();
    expect(liveWebcam(rule, view('alpha', 0.6), noon, webcams)).not.toBeNull();
    expect(liveWebcam(ruleOf(['summit'], 0.2), view('alpha', 0.3), noon, webcams)).not.toBeNull();
    expect(liveWebcam(ruleOf(['summit']), view('alpha', 0.59), noon, webcams)).toBeNull();
  });

  it('takes the first position of the rule that the station has', () => {
    const rules = ruleOf(['slopes', 'village', 'summit']);
    expect(liveWebcam(rules, view('alpha', 0.9), noon, webcams)?.webcam.id).toBe('village');
    expect(liveWebcam(ruleOf(['nordic']), view('alpha', 0.9), noon, webcams)).toBeNull();
  });

  it('shows nothing without a rule, a webcam, a live view or a leader', () => {
    expect(liveWebcam({}, view('alpha', 0.9), noon, webcams)).toBeNull();
    expect(liveWebcam(rule, view('beta', 0.9), noon, webcams)).toBeNull();
    expect(liveWebcam(rule, view('alpha', 0.9, 'historical'), noon, webcams)).toBeNull();
    expect(liveWebcam(rule, null, noon, webcams)).toBeNull();
    const empty = { ...view('alpha', 0.9), items: [] } as KpiView;
    expect(liveWebcam(rule, empty, noon, webcams)).toBeNull();
  });

  it('starts with the bluebird tile and the summit webcam of Cauterets', () => {
    const withRule = tiles.filter((t) => t.webcam);
    expect(withRule.map((t) => t.id)).toEqual(['bluebird_day']);
    expect(withRule[0]!.webcam!.positions).toEqual(['summit']);
    const cauterets = stationWebcams.get('pyrenees/cauterets') ?? [];
    expect(cauterets.find((w) => w.position === 'summit')?.url).toBe(
      'https://www.skaping.com/cauterets/les-cretes/panoramique',
    );
  });
});
