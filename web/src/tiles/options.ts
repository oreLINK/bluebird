/**
 * Read typed values from a tile's free-form `options` (config/tiles.yaml),
 * falling back to a default when the option is missing or has the wrong type.
 */
import type { Tile } from '../lib/config';

type Options = Record<string, unknown> | undefined;

export function numberOption(options: Options, key: string, fallback: number): number {
  const value = options?.[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

export function booleanOption(options: Options, key: string, fallback: boolean): boolean {
  const value = options?.[key];
  return typeof value === 'boolean' ? value : fallback;
}

export function stringOption(options: Options, key: string, fallback: string): string {
  const value = options?.[key];
  return typeof value === 'string' ? value : fallback;
}

/** Illustrations available for the banner of a `banner` tile (see BannerArt.svelte). */
export const BANNER_SCENES = ['snowfall', 'piste', 'offpiste', 'mountain'] as const;
export type BannerScene = (typeof BANNER_SCENES)[number];

const SCENE_BY_ICON: Record<string, BannerScene> = {
  snowflake: 'snowfall',
  piste: 'piste',
  mountain: 'offpiste',
};

/** `options.scene` when valid, otherwise a scene matching the tile icon. */
export function bannerScene(tile: Pick<Tile, 'options' | 'icon'>): BannerScene {
  const scene = stringOption(tile.options, 'scene', '');
  if ((BANNER_SCENES as readonly string[]).includes(scene)) return scene as BannerScene;
  return SCENE_BY_ICON[tile.icon ?? ''] ?? 'mountain';
}
