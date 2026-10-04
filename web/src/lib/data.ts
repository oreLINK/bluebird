/**
 * Fetch diamond payloads published by the pipeline.
 *
 * Production: `gh-pages/data/diamond/{massif}/latest.json` and
 * `gh-pages/data/diamond/status.json`, rewritten by every refresh (00:00,
 * 06:00, 12:00 and 18:00 Paris time). Development: the demo files committed in
 * `web/public/data/diamond/` (regenerate them with `uv run bluebird demo`).
 */
import type { DiamondMassifDaily } from './generated/diamond-massif-daily';
import type { DiamondStatus } from './generated/diamond-status';

export type MassifDaily = DiamondMassifDaily;
export type KpiPeriod = DiamondMassifDaily['kpis'][string]['periods'][number];
export type RankingEntry = KpiPeriod['ranking'][number];
export type StationInfo = DiamondMassifDaily['stations'][string];
export type ServiceStatus = DiamondStatus;

export const SUPPORTED_SCHEMA_VERSION = 2;
export const SUPPORTED_STATUS_VERSION = 1;

export class DataError extends Error {}

export function latestUrl(massifId: string, base: string = import.meta.env.BASE_URL): string {
  return `${base}data/diamond/${encodeURIComponent(massifId)}/latest.json`;
}

export function statusUrl(base: string = import.meta.env.BASE_URL): string {
  return `${base}data/diamond/status.json`;
}

async function loadJson<T extends { schema_version?: number }>(
  url: string,
  version: number,
  fetchImpl: typeof fetch,
): Promise<T | null> {
  const response = await fetchImpl(url, { cache: 'no-cache' });
  if (response.status === 404) return null;
  if (!response.ok) throw new DataError(`HTTP ${response.status} for ${url}`);
  const payload = (await response.json()) as T;
  if (payload.schema_version !== version) {
    throw new DataError(`unsupported schema_version ${String(payload.schema_version)}`);
  }
  return payload;
}

/**
 * Load the latest payload of a massif. Resolves to `null` when nothing has
 * been published yet (HTTP 404); rejects on network or format errors.
 */
export function loadMassif(
  massifId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<MassifDaily | null> {
  return loadJson<MassifDaily>(latestUrl(massifId), SUPPORTED_SCHEMA_VERSION, fetchImpl);
}

/** Load the state of the last refresh (footer). Same contract as `loadMassif`. */
export function loadStatus(fetchImpl: typeof fetch = fetch): Promise<ServiceStatus | null> {
  return loadJson<ServiceStatus>(statusUrl(), SUPPORTED_STATUS_VERSION, fetchImpl);
}

/** Today's date (YYYY-MM-DD) in a given IANA timezone. */
export function todayIn(timeZone: string, now: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone }).format(now);
}
