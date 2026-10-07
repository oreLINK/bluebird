import { describe, expect, it } from 'vitest';
import { type Massif, type SiteDomain, type SiteStation, massifs, siteStations } from './config';
import { nextPath } from './filterLevels';
import { flagOf, geoState, readGeoPath } from './geoLevels';

const name = (fr: string) => ({ fr, en: fr });
const alps = {
  id: 'alpes-du-nord',
  name: name('Alpes du Nord'),
  bbox: [5, 45, 7.5, 46.5],
  zones: [
    { id: 'haute-savoie', name: name('Haute-Savoie'), code: '74' },
    { id: 'savoie', name: name('Savoie'), code: '73' },
    { id: 'valais', name: name('Valais'), country: 'CH' },
    { id: 'isere', name: name('Isère'), code: '38' }, // no station: no chip
    { id: 'aoste', name: name("Val d'Aoste"), country: 'IT' },
    { id: 'ain', name: name('Ain'), code: '01' }, // listed after foreign zones, shown before them
  ],
} as Massif;
const jura = { id: 'jura', name: name('Jura'), bbox: [5, 46, 7, 47.5], zones: [{ id: 'doubs', name: name('Doubs') }] } as Massif;
const all = [alps, jura];
const st = (id: string, massifId: string, zone?: string, domain?: string): SiteStation => ({ id, massifId, zone, domain });
const stations = [
  st('avoriaz', 'alpes-du-nord', 'haute-savoie', 'portes-du-soleil'),
  st('morzine', 'alpes-du-nord', 'haute-savoie', 'portes-du-soleil'),
  st('la-clusaz', 'alpes-du-nord', 'haute-savoie'),
  st('champery', 'alpes-du-nord', 'valais', 'portes-du-soleil'),
  st('val-thorens', 'alpes-du-nord', 'savoie', 'trois-vallees'),
  st('meribel', 'alpes-du-nord', 'savoie', 'trois-vallees'),
  st('la-plagne', 'alpes-du-nord', 'savoie', 'solo'), // a domain of one station: no chip
  st('metabief', 'jura', 'doubs'),
  st('la-thuile', 'alpes-du-nord', 'aoste'),
  st('les-plans', 'alpes-du-nord', 'ain'),
];
const domains: SiteDomain[] = [
  { id: 'portes-du-soleil', massifId: 'alpes-du-nord', name: 'Portes du Soleil' },
  { id: 'trois-vallees', massifId: 'alpes-du-nord', name: 'Les 3 Vallées' },
  { id: 'solo', massifId: 'alpes-du-nord', name: 'Solo' },
];
const keys = (s: ReturnType<typeof geoState>) => s.chips.map((c) => `${c.key}${c.pressed ? '*' : ''}`);
const ids = (s: ReturnType<typeof geoState>) => (s.stationIds ? [...s.stationIds].sort() : null);

describe('geoState', () => {
  it('lists the massifs and keeps the last one on the page when none is chosen', () => {
    const state = geoState([], all, stations, domains, 'jura');
    expect(keys(state)).toEqual(['1:alpes-du-nord', '1:jura']);
    expect(state.massifId).toBe('jura');
    expect(state.stationIds).toBeNull();
  });

  it('offers the zones with stations, then narrows to one zone', () => {
    const massif = geoState(['alpes-du-nord'], all, stations, domains, '');
    // The French départements first, then the foreign regions with their flag.
    expect(keys(massif)).toEqual([
      '1:alpes-du-nord*',
      '2:haute-savoie',
      '2:savoie',
      '2:ain',
      '2:valais',
      '2:aoste',
    ]);
    expect(massif.chips.map((c) => c.name.fr).slice(3)).toEqual(['Ain', '🇨🇭 Valais', "🇮🇹 Val d'Aoste"]);
    expect(massif.stationIds).toBeNull();

    const savoie = geoState(['alpes-du-nord', 'savoie'], all, stations, domains, '');
    expect(keys(savoie)).toEqual(['1:alpes-du-nord*', '2:savoie*', '3:trois-vallees']);
    expect(ids(savoie)).toEqual(['la-plagne', 'meribel', 'val-thorens']);
  });

  it('keeps every station of a linked area, across zones and borders', () => {
    const valais = geoState(['alpes-du-nord', 'valais'], all, stations, domains, '');
    expect(keys(valais)).toEqual(['1:alpes-du-nord*', '2:valais*', '3:portes-du-soleil']);
    const pds = geoState(['alpes-du-nord', 'valais', 'portes-du-soleil'], all, stations, domains, '');
    expect(ids(pds)).toEqual(['avoriaz', 'champery', 'morzine']);
    expect(pds.chips.at(-1)?.name.fr).toBe('Portes du Soleil');
  });

  it('skips a single zone and drops unknown path items', () => {
    const doubs = geoState(['jura', 'doubs'], all, stations, domains, '');
    expect(keys(doubs)).toEqual(['1:jura*']);
    expect(doubs.path).toEqual(['jura']);
    expect(geoState(['alpes-du-nord', 'nowhere'], all, stations, domains, '').path).toEqual(['alpes-du-nord']);
  });

  it('removes a chosen place with the levels after it', () => {
    const pds = geoState(['alpes-du-nord', 'haute-savoie', 'portes-du-soleil'], all, stations, domains, '');
    expect(nextPath(pds.path, pds.chips[1]!)).toEqual(['alpes-du-nord']);
  });

  it('turns a country code into its flag', () => {
    expect(flagOf('ES')).toBe('🇪🇸');
    expect(flagOf('AD')).toBe('🇦🇩');
    expect(flagOf('es')).toBe('');
    expect(flagOf(null)).toBe('');
  });

  it('reads the stored place, or the former massif preference', () => {
    expect(readGeoPath('pyrenees/ariege', null)).toEqual(['pyrenees', 'ariege']);
    expect(readGeoPath(null, 'pyrenees')).toEqual(['pyrenees']);
    expect(readGeoPath(null, null)).toEqual([]);
  });

  it('bundles the five Pyrenean départements', () => {
    const state = geoState(['pyrenees'], massifs, siteStations, [], '');
    expect(state.chips.map((c) => c.name.fr)).toEqual([
      'Pyrénées',
      'Pyrénées-Atlantiques',
      'Hautes-Pyrénées',
      'Haute-Garonne',
      'Ariège',
      'Pyrénées-Orientales',
    ]);
    const hp = geoState(['pyrenees', 'hautes-pyrenees'], massifs, siteStations, [], '');
    expect(hp.stationIds?.size).toBe(7);
  });
});
