import { readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { buildPhotoIndex, isStationPhotoKey, listCredits, photoKeys, pickPhoto, stationPhotoKeys } from './photos';

const index = buildPhotoIndex({
  '../assets/photos/pyrenees/cauterets/cauterets_2.webp': '/assets/cauterets-2.webp',
  '../assets/photos/pyrenees/cauterets/cauterets_10.jpg': '/assets/cauterets-10.jpg',
  '../assets/photos/pyrenees/cauterets/cauterets_1.jpg': '/assets/cauterets-1.jpg',
  '../assets/photos/pyrenees/massif.jpg': '/assets/pyrenees.jpg',
});
const credits = { 'pyrenees/cauterets/cauterets_1': { author: 'Jane Doe', license: 'CC BY 4.0' } };

describe('photos', () => {
  it('lists the photos of a station in number order', () => {
    expect(stationPhotoKeys(index, 'pyrenees', 'cauterets')).toEqual([
      'pyrenees/cauterets/cauterets_1',
      'pyrenees/cauterets/cauterets_2',
      'pyrenees/cauterets/cauterets_10',
    ]);
  });

  it('draws a random photo of the station ranked first, with its credit', () => {
    expect(pickPhoto('leader', 'pyrenees', 'cauterets', index, credits, () => 0)).toEqual({
      key: 'pyrenees/cauterets/cauterets_1',
      url: '/assets/cauterets-1.jpg',
      credit: { author: 'Jane Doe', license: 'CC BY 4.0' },
    });
    expect(pickPhoto('leader', 'pyrenees', 'cauterets', index, credits, () => 0.99)?.key).toBe(
      'pyrenees/cauterets/cauterets_10',
    );
  });

  it('falls back to no photo when the leader has none or the option is none', () => {
    expect(pickPhoto('leader', 'pyrenees', 'gourette', index, credits)).toBeUndefined();
    expect(pickPhoto('leader', 'pyrenees', undefined, index, credits)).toBeUndefined();
    expect(pickPhoto('none', 'pyrenees', 'cauterets', index, credits)).toBeUndefined();
  });

  it('supports a fixed photo path', () => {
    expect(pickPhoto('pyrenees/massif', 'pyrenees', 'x', index, credits)?.url).toBe('/assets/pyrenees.jpg');
  });

  it('recognises the station photo naming convention', () => {
    expect(isStationPhotoKey('pyrenees/cauterets/cauterets_1')).toBe(true);
    expect(isStationPhotoKey('pyrenees/cauterets/cauterets')).toBe(false);
    expect(isStationPhotoKey('pyrenees/cauterets/gourette_1')).toBe(false);
    expect(isStationPhotoKey('pyrenees/cauterets/photo')).toBe(false);
  });
});

describe('photo folders', () => {
  const stationFiles = import.meta.glob('@config/stations/*.yaml', { eager: true, import: 'default' }) as Record<
    string,
    { stations: { id: string }[] }
  >;
  const photosDir = fileURLToPath(new URL('../assets/photos/', import.meta.url));

  it('has one folder per massif and station', () => {
    for (const [path, file] of Object.entries(stationFiles)) {
      const massifId = path.split('/').pop()!.replace('.yaml', '');
      const folders = readdirSync(photosDir + massifId);
      for (const station of file.stations) expect(folders, `${massifId}/${station.id}`).toContain(station.id);
    }
  });

  it('names station photos <station_id>_<n> inside their station folder', () => {
    for (const key of photoKeys()) {
      if (key.split('/').length === 3) expect(isStationPhotoKey(key), key).toBe(true);
    }
  });
});

describe('listCredits', () => {
  it('keeps the credits of existing photos, sorted by key', () => {
    const index = new Map([
      ['pyrenees/b/b_1', '/b.webp'],
      ['pyrenees/a/a_1', '/a.webp'],
    ]);
    const credit = { author: 'X' };
    const list = listCredits(index, {
      'pyrenees/b/b_1': credit,
      'pyrenees/a/a_1': credit,
      'pyrenees/gone/gone_1': credit,
    });
    expect(list.map((c) => c.key)).toEqual(['pyrenees/a/a_1', 'pyrenees/b/b_1']);
  });
});
