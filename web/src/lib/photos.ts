/**
 * Photos for tile banners, bundled from `src/assets/photos/` at build time.
 *
 * Tile option `photo` (config/tiles.yaml):
 *   - `none` (default): no photo, the tile shows its illustration;
 *   - `leader`: a random photo of the station ranked first, among
 *     `<massif_id>/<station_id>/<station_id>_<n>.*` (n = 1, 2, 3…). The draw
 *     happens once per station and page load, so the photo stays stable;
 *   - any other value: a fixed photo at that path (without extension).
 * When the photo does not exist, the illustration is shown instead.
 */
import creditsYaml from '../assets/photos/credits.yaml';

export interface PhotoCredit {
  author: string;
  license?: string;
  url?: string;
}

export interface Photo {
  key: string;
  url: string;
  credit?: PhotoCredit;
}

const PHOTO_EXTENSION = /\.(webp|jpe?g|png|avif)$/i;
const ROOT = '../assets/photos/';

/** Map `pyrenees/cauterets/cauterets_1` → bundled URL, from an `import.meta.glob` result. */
export function buildPhotoIndex(files: Record<string, string>): Map<string, string> {
  const index = new Map<string, string>();
  for (const [path, url] of Object.entries(files)) {
    const key = path.replace(ROOT, '').replace(PHOTO_EXTENSION, '');
    index.set(key, url);
  }
  return index;
}

/** Key of photo number `n` of a station: `<massif_id>/<station_id>/<station_id>_<n>`. */
export function stationPhotoKey(massifId: string, stationId: string, n: number): string {
  return `${massifId}/${stationId}/${stationId}_${n}`;
}

/** Whether a key follows the station photo convention (`<massif>/<id>/<id>_<n>`). */
export function isStationPhotoKey(key: string): boolean {
  const [massifId, stationId, file, ...extra] = key.split('/');
  return (
    !!massifId && !!stationId && !extra.length && new RegExp(`^${stationId}_\\d+$`).test(file ?? '')
  );
}

/** Every photo of a station, ordered by number. */
export function stationPhotoKeys(
  index: Map<string, string>,
  massifId: string,
  stationId: string,
): string[] {
  const prefix = `${massifId}/${stationId}/${stationId}_`;
  return [...index.keys()]
    .filter((key) => key.startsWith(prefix) && /^\d+$/.test(key.slice(prefix.length)))
    .sort((a, b) => Number(a.slice(prefix.length)) - Number(b.slice(prefix.length)));
}

/** Credits of the photos that exist, sorted by key (for the legal page). */
export function listCredits(
  index: Map<string, string>,
  credits: Record<string, PhotoCredit>,
): { key: string; credit: PhotoCredit }[] {
  return Object.keys(credits)
    .filter((key) => index.has(key))
    .sort()
    .map((key) => ({ key, credit: credits[key]! }));
}

/** Resolve the `photo` option of a tile against the available photos. */
export function pickPhoto(
  option: string,
  massifId: string,
  leaderStationId: string | undefined,
  index: Map<string, string>,
  credits: Record<string, PhotoCredit>,
  random: () => number = Math.random,
): Photo | undefined {
  if (!option || option === 'none') return undefined;
  let key: string | undefined = option;
  if (option === 'leader') {
    const candidates = leaderStationId
      ? stationPhotoKeys(index, massifId, leaderStationId)
      : [];
    key = candidates[Math.floor(random() * candidates.length)];
  }
  if (!key) return undefined;
  const url = index.get(key);
  return url ? { key, url, credit: credits[key] } : undefined;
}

const files = import.meta.glob('../assets/photos/**/*.{webp,jpg,jpeg,png,avif,WEBP,JPG,JPEG,PNG,AVIF}', {
  eager: true,
  query: '?url',
  import: 'default',
}) as Record<string, string>;

const index = buildPhotoIndex(files);
const credits = (creditsYaml ?? {}) as Record<string, PhotoCredit>;

/** Every bundled photo with its credit. */
export const photoCredits = listCredits(index, credits);

/** Photo drawn for each station in this page load, so re-renders keep it. */
const drawn = new Map<string, Photo | undefined>();

export function tilePhoto(
  option: string,
  massifId: string,
  leaderStationId: string | undefined,
): Photo | undefined {
  if (option !== 'leader') return pickPhoto(option, massifId, leaderStationId, index, credits);
  const station = `${massifId}/${leaderStationId}`;
  if (!drawn.has(station)) {
    drawn.set(station, pickPhoto(option, massifId, leaderStationId, index, credits));
  }
  return drawn.get(station);
}

/** Keys of every bundled photo (used by tests to check the folder convention). */
export function photoKeys(): string[] {
  return [...index.keys()];
}
