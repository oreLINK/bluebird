/**
 * Compact header (pure, unit-tested): the two chip bars of the header fold
 * away while the page scrolls down and come back when it scrolls up; folded,
 * one row recalls the chosen place and the chosen filter (two pills at most).
 */
import type { FilterChip } from './filterLevels';

export interface ScrollState {
  /** The chip bars are folded. */
  collapsed: boolean;
  /**
   * Scroll position the next move is measured from: the lowest point reached
   * while open, the highest while folded, so small back-and-forth moves do
   * nothing.
   */
  anchor: number;
}

export interface ScrollOptions {
  /** Above this scroll position (px) the bars always stay open. */
  minY: number;
  /** Distance (px) to scroll in one direction before folding or opening. */
  threshold: number;
}

export const SCROLL_OPTIONS: ScrollOptions = { minY: 96, threshold: 12 };

/** Next state after the page scrolled to `y`. */
export function nextScrollState(
  state: ScrollState,
  y: number,
  options: ScrollOptions = SCROLL_OPTIONS,
): ScrollState {
  if (y <= options.minY) return { collapsed: false, anchor: y };
  const delta = y - state.anchor;
  if (!state.collapsed && delta > options.threshold) return { collapsed: true, anchor: y };
  if (state.collapsed && delta < -options.threshold) return { collapsed: false, anchor: y };
  // Follow the current direction: open → lowest point, folded → highest point.
  if (state.collapsed ? y > state.anchor : y < state.anchor) return { ...state, anchor: y };
  return state;
}

export interface HeaderSummary {
  /** The deepest chosen place (massif, zone or linked area), if any. */
  place: FilterChip | null;
  /** The chosen filter levels, level 1 first; empty when no filter is chosen. */
  filter: FilterChip[];
}

/** What the folded header recalls: at most one place pill and one filter pill. */
export function headerSummary(places: FilterChip[], filters: FilterChip[]): HeaderSummary {
  const chosenPlaces = places.filter((c) => c.pressed).sort((a, b) => a.level - b.level);
  return {
    place: chosenPlaces.at(-1) ?? null,
    filter: filters.filter((c) => c.pressed).sort((a, b) => a.level - b.level),
  };
}
