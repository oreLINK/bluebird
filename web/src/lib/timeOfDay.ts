/**
 * Phase of the day (pure, unit-tested). The header logo tints the lens of its
 * ski goggle with one gradient per phase (tokens `--logo-lens-<phase>-<n>` in
 * styles/tokens.css). The favicon and the home-screen icon always use `day`.
 */
export type DayPhase = 'dawn' | 'day' | 'dusk' | 'night';

/** Local hour (0–23) each phase starts at, in chronological order. */
export const PHASE_STARTS: ReadonlyArray<readonly [DayPhase, number]> = [
  ['dawn', 6],
  ['day', 9],
  ['dusk', 17],
  ['night', 20],
];

/** Hour of the day (0–23) of `now` in an IANA timezone. */
export function localHour(now: Date, timezone: string): number {
  const hour = new Intl.DateTimeFormat('en-GB', {
    timeZone: timezone,
    hour: '2-digit',
    hourCycle: 'h23',
  }).format(now);
  return Number.parseInt(hour, 10);
}

/** Phase of the day at `now` in an IANA timezone; before 06:00 is still night. */
export function dayPhase(now: Date, timezone: string): DayPhase {
  const hour = localHour(now, timezone);
  let phase: DayPhase = 'night';
  for (const [id, start] of PHASE_STARTS) {
    if (hour >= start) phase = id;
  }
  return phase;
}
