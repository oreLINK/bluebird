/**
 * Everything a tile shows, derived from its configuration and a KpiView
 * (lib/kpiView.ts). Shared by every tile type, for live and historical KPIs.
 */
import { type Filter, type Tile, filters as configFilters, massifs } from '../lib/config';
import type { Localized } from '../lib/generated/kpis';
import { type KpiView, type RankItem, showsPercent } from '../lib/kpiView';
import { type Photo, tilePhoto } from '../lib/photos';
import { type TimeWindow, sharedWindow, splitTop } from '../lib/ranking';
import { type BannerScene, bannerScene, booleanOption, numberOption, stringOption } from './options';

/** Colour theme of a tile: token overrides on its card (styles/base.css `[data-tile-theme]`). */
export const TILE_THEMES = ['default', 'rewind'] as const;
export type TileTheme = (typeof TILE_THEMES)[number];

export interface TileModel {
  view: KpiView;
  items: RankItem[];
  top: RankItem[];
  rest: RankItem[];
  /** Decimal odds next to probabilities (live KPIs shown as a percent only). */
  showOdds: boolean;
  /** Tapping a station shows its details (live only; option `details`, off for now). */
  details: boolean;
  scene: BannerScene;
  skyline: number[];
  photo: Photo | undefined;
  /** Time window shared by every station (live only). */
  timeWindow: TimeWindow | null;
  theme: TileTheme;
  /** Small label on the tile, e.g. the Rewind name for historical KPIs. */
  badge: Localized | undefined;
  /** Live only: when the values were computed, if by an earlier refresh than the page's. */
  staleSince: string | null;
  /** i18n key of the message shown when the ranking is empty. */
  emptyMessage: 'tile.noRanking' | 'rewind.noData';
}

/**
 * Theme of a tile: option `theme` when valid, else the theme of the Rewind's
 * filter for a historical KPI (Christmas red for the Rewinds), else default.
 */
export function tileTheme(tile: Pick<Tile, 'options'>, view: KpiView, filters: Filter[]): TileTheme {
  const option = stringOption(tile.options, 'theme', '');
  if ((TILE_THEMES as readonly string[]).includes(option)) return option as TileTheme;
  if (view.kind === 'historical') {
    const theme = filters.find((f) => f.id === view.rewind.filter)?.theme;
    if (theme && (TILE_THEMES as readonly string[]).includes(theme)) return theme as TileTheme;
  }
  return 'default';
}

export function tileModel(tile: Tile, view: KpiView, filters: Filter[] = configFilters): TileModel {
  const live = view.kind === 'live';
  const topCount = Math.min(3, Math.max(1, numberOption(tile.options, 'top', 3)));
  const { top, rest } = splitTop(view.items, topCount);
  return {
    view,
    items: view.items,
    top,
    rest,
    showOdds: showsPercent(view) && booleanOption(tile.options, 'show_odds', false),
    details: live && booleanOption(tile.options, 'details', false),
    scene: bannerScene(tile),
    skyline: massifs.find((m) => m.id === view.massifId)?.skyline ?? [],
    photo: tilePhoto(stringOption(tile.options, 'photo', 'none'), view.massifId, view.items[0]?.stationId),
    timeWindow: live ? sharedWindow(view.ranking) : null,
    theme: tileTheme(tile, view, filters),
    badge: view.kind === 'historical' ? view.rewind.name : undefined,
    staleSince: view.kind === 'live' && view.stale ? view.generatedAt : null,
    emptyMessage: live ? 'tile.noRanking' : 'rewind.noData',
  };
}
