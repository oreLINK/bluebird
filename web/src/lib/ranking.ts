/** Pure helpers shared by the tiles that display a KPI ranking (unit-tested). */
import type { RankingEntry } from './data';

export interface TimeWindow {
  start: string;
  end: string;
}

/** The time window shared by every entry, or `null` when stations differ. */
export function sharedWindow(ranking: readonly RankingEntry[]): TimeWindow | null {
  const first = ranking[0];
  if (!first) return null;
  const same = ranking.every(
    (r) => r.window_start === first.window_start && r.window_end === first.window_end,
  );
  return same ? { start: first.window_start, end: first.window_end } : null;
}

/** Split a ranking into its `count` first entries and the rest. */
export function splitTop<T>(ranking: readonly T[], count: number): { top: T[]; rest: T[] } {
  const n = Math.max(0, Math.floor(count));
  return { top: ranking.slice(0, n), rest: ranking.slice(n) };
}

export type ConfidenceLevel = RankingEntry['confidence'];

export interface Reliability {
  /** 0..1: mean of the station confidences (high = 1, medium = 0.5, low = 0). */
  score: number;
  level: ConfidenceLevel;
  counts: Record<ConfidenceLevel, number>;
  /** Fewest ensemble scenarios used for a station. */
  members: number;
}

const CONFIDENCE_SCORE: Record<ConfidenceLevel, number> = { high: 1, medium: 0.5, low: 0 };

/** Overall reliability of a KPI today, from the confidence of every station. */
export function reliability(ranking: readonly RankingEntry[]): Reliability | null {
  if (ranking.length === 0) return null;
  const counts: Record<ConfidenceLevel, number> = { high: 0, medium: 0, low: 0 };
  for (const entry of ranking) counts[entry.confidence] += 1;
  const score =
    ranking.reduce((sum, entry) => sum + CONFIDENCE_SCORE[entry.confidence], 0) / ranking.length;
  const level: ConfidenceLevel = score >= 2 / 3 ? 'high' : score >= 1 / 3 ? 'medium' : 'low';
  return { score, level, counts, members: Math.min(...ranking.map((e) => e.members)) };
}
