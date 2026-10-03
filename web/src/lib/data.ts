/**
 * Fetch diamond payloads published by the pipeline.
 *
 * Production: `gh-pages/data/diamond/{massif}/latest.json`, written every
 * morning by the daily workflow. Development: the demo files committed in
 * `web/public/data/diamond/` (regenerate them with `uv run bluebird demo`).
 */
import type { DiamondMassifDaily } from './generated/diamond-massif-daily';

export type MassifDaily = DiamondMassifDaily;
export type RankingEntry = DiamondMassifDaily['kpis'][string]['ranking'][number];

export const SUPPORTED_SCHEMA_VERSION = 1;

export class DataError extends Error {}

export function latestUrl(massifId: string, base: string = import.meta.env.BASE_URL): string {
  return `${base}data/diamond/${encodeURIComponent(massifId)}/latest.json`;
}

/**
 * Load the latest payload of a massif. Resolves to `null` when nothing has
 * been published yet (HTTP 404); rejects on network or format errors.
 */
export async function loadMassif(
  massifId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<MassifDaily | null> {
  const response = await fetchImpl(latestUrl(massifId), { cache: 'no-cache' });
  if (response.status === 404) return null;
  if (!response.ok) throw new DataError(`HTTP ${response.status} for ${massifId}`);
  const payload = (await response.json()) as MassifDaily;
  if (payload.schema_version !== SUPPORTED_SCHEMA_VERSION) {
    throw new DataError(`unsupported schema_version ${String(payload.schema_version)}`);
  }
  return payload;
}

/** Today's date (YYYY-MM-DD) in a given IANA timezone. */
export function todayIn(timeZone: string, now: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone }).format(now);
}

/** Best probability of a KPI across stations (0 when absent). */
export function maxProbability(payload: MassifDaily | null | undefined, kpiId: string): number {
  const ranking = payload?.kpis[kpiId]?.ranking ?? [];
  return ranking.reduce((max, entry) => Math.max(max, entry.probability), 0);
}
