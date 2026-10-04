/**
 * Data shared by the banner tile types (TileBanner, TileBannerFull), derived
 * from the tile configuration and the diamond payload.
 */
import { type Kpi, type Tile, massifs } from '../lib/config';
import type { RankingEntry } from '../lib/data';
import type { MassifView } from '../lib/periods';
import { type Photo, tilePhoto } from '../lib/photos';
import { type TimeWindow, sharedWindow, splitTop } from '../lib/ranking';
import { type BannerScene, bannerScene, booleanOption, numberOption, stringOption } from './options';

export interface BannerModel {
  kpi: Kpi | undefined;
  ranking: RankingEntry[];
  top: RankingEntry[];
  rest: RankingEntry[];
  showOdds: boolean;
  scene: BannerScene;
  skyline: number[];
  timeWindow: TimeWindow | null;
  photo: Photo | undefined;
  /** When the values were computed, if by an earlier refresh than the page's. */
  staleSince: string | null;
}

export function bannerModel(tile: Tile, kpis: Kpi[], data: MassifView): BannerModel {
  const kpi = kpis[0];
  const view = kpi ? data.kpis[kpi.id] : undefined;
  const ranking = view?.ranking ?? [];
  const topCount = Math.min(3, Math.max(1, numberOption(tile.options, 'top', 3)));
  const { top, rest } = splitTop(ranking, topCount);
  return {
    kpi,
    ranking,
    top,
    rest,
    showOdds: booleanOption(tile.options, 'show_odds', false),
    scene: bannerScene(tile),
    skyline: massifs.find((m) => m.id === data.massif_id)?.skyline ?? [],
    timeWindow: sharedWindow(ranking),
    photo: tilePhoto(
      stringOption(tile.options, 'photo', 'none'),
      data.massif_id,
      ranking[0]?.station_id,
    ),
    staleSince: view?.stale ? view.generated_at : null,
  };
}
