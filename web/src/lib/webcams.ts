/**
 * Live webcam link of a tile (pure, unit-tested).
 *
 * A live tile with a `webcam` rule (config/tiles.yaml) links the official page
 * of the leading station's webcam from a LIVE badge when:
 *   - the period shown is in progress (so today's, never tomorrow's),
 *   - the station ranked first has a webcam at one of the rule's positions
 *     (config/stations/<massif>.yaml `webcams`; the first position that
 *     matches wins),
 *   - its probability reaches `min_probability`.
 * The webcam image itself is never shown on the site (no reuse rights).
 */
import type { Tile, Webcam } from './config';
import type { KpiView } from './kpiView';

export interface LiveWebcam {
  stationId: string;
  webcam: Webcam;
}

/** Probability needed when the rule does not set one (same default as config.py). */
export const DEFAULT_MIN_PROBABILITY = 0.6;

export function liveWebcam(
  tile: Pick<Tile, 'webcam'>,
  view: KpiView | null,
  now: number,
  webcams: Map<string, Webcam[]>,
): LiveWebcam | null {
  const rule = tile.webcam;
  if (!rule || !view || view.kind !== 'live' || !view.slot) return null;
  const start = Date.parse(view.slot.start);
  const end = Date.parse(view.slot.end);
  if (!(now >= start && now < end)) return null;
  const leader = view.items[0];
  if (!leader) return null;
  const probability = leader.entry?.probability ?? leader.value;
  if (!(probability >= (rule.min_probability ?? DEFAULT_MIN_PROBABILITY))) return null;
  const cams = webcams.get(`${view.massifId}/${leader.stationId}`) ?? [];
  for (const position of rule.positions) {
    const webcam = cams.find((w) => w.position === position);
    if (webcam) return { stationId: leader.stationId, webcam };
  }
  return null;
}
