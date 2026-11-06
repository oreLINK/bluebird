import { describe, expect, it } from 'vitest';
import type { FilterChip } from './filterLevels';
import { type ScrollState, headerSummary, nextScrollState } from './compactHeader';

const opts = { minY: 100, threshold: 10 };
const run = (ys: number[], start: ScrollState = { collapsed: false, anchor: 0 }) =>
  ys.reduce((s, y) => nextScrollState(s, y, opts), start);

describe('nextScrollState', () => {
  it('stays open near the top of the page, whatever the direction', () => {
    expect(run([40, 90, 60, 100]).collapsed).toBe(false);
  });

  it('folds after scrolling down past the threshold, below the top zone', () => {
    expect(run([90, 105]).collapsed).toBe(true); // 15 px down from 90, and past the top zone
    expect(run([95, 104]).collapsed).toBe(false); // only 9 px down
    expect(run([150]).collapsed).toBe(true);
  });

  it('opens again after scrolling up past the threshold', () => {
    const folded = run([300]);
    expect(folded.collapsed).toBe(true);
    expect(nextScrollState(folded, 295, opts).collapsed).toBe(true);
    expect(nextScrollState(folded, 289, opts).collapsed).toBe(false);
  });

  it('measures from the highest point while folded and the lowest while open', () => {
    const folded = run([300, 500]); // still going down: anchor follows
    expect(folded).toEqual({ collapsed: true, anchor: 500 });
    const reopened = run([300, 500, 480]);
    expect(reopened).toEqual({ collapsed: false, anchor: 480 });
    expect(run([300, 500, 480, 470]).anchor).toBe(470); // open: follows the way up
    expect(run([300, 500, 480, 470, 478]).collapsed).toBe(false); // 8 px down: not yet
    expect(run([300, 500, 480, 470, 481]).collapsed).toBe(true);
  });

  it('opens when the page jumps back to the top', () => {
    expect(nextScrollState({ collapsed: true, anchor: 800 }, 0, opts)).toEqual({ collapsed: false, anchor: 0 });
  });
});

const chip = (key: string, level: number, pressed: boolean): FilterChip => ({
  key,
  id: key,
  level,
  name: { fr: key, en: key, es: key },
  pressed,
});

describe('headerSummary', () => {
  it('recalls the deepest chosen place and every chosen filter level', () => {
    const places = [chip('pyrenees', 1, true), chip('hautes-pyrenees', 2, true), chip('ariege', 2, false)];
    const filters = [chip('d0', 3, true), chip('sky', 1, true), chip('sun', 2, true), chip('d1', 3, false)];
    const summary = headerSummary(places, filters);
    expect(summary.place?.key).toBe('hautes-pyrenees');
    expect(summary.filter.map((c) => c.key)).toEqual(['sky', 'sun', 'd0']);
  });

  it('has no filter pill when no filter is chosen', () => {
    const summary = headerSummary([chip('pyrenees', 1, true)], [chip('snow', 1, false), chip('sky', 1, false)]);
    expect(summary).toEqual({ place: chip('pyrenees', 1, true), filter: [] });
  });

  it('has no place pill when no place is chosen', () => {
    expect(headerSummary([chip('pyrenees', 1, false)], []).place).toBeNull();
  });
});
