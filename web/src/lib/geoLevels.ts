/**
 * Levels of the massif bar, like the filter bar (lib/filterLevels.ts), but for
 * places (unit-tested):
 *   1. massif        config/massifs.yaml (Pyrénées, Alpes du Nord…)
 *   2. zone          its `zones`: the département in France, the country or
 *                    region abroad (Andorre, Aragon, Valais…); skipped below
 *                    two zones with stations. One mixed list: the French
 *                    zones first, then the foreign ones with their flag
 *                    (🇪🇸 Aragon, 🇦🇩 Andorre)
 *   3. linked area   `domains` of config/stations/<massif>.yaml with at least
 *                    two stations, offered under every zone where it has one;
 *                    choosing it keeps all its stations, whatever their zone or
 *                    country (Portes du Soleil: Avoriaz, Morzine, Champéry)
 * The page always shows one massif (its refreshed payload): removing the
 * massif chip lists the massifs again and keeps the last one on the page.
 * Tiles keep ranking stations, restricted to the chosen place (`stationIds`).
 */
import type { Massif, SiteDomain, SiteStation } from './config';
import type { FilterChip } from './filterLevels';
import type { Localized } from './generated/massifs';

export interface GeoState {
  /** The path actually applied: `[massif]`, `[massif, zone]`, `[massif, zone, domain]`. */
  path: string[];
  chips: FilterChip[];
  /** The massif whose data the page shows. */
  massifId: string;
  /** Stations to rank; `null` for every station of the massif. */
  stationIds: Set<string> | null;
}

/** The site's home country: its zones come first and carry no flag. */
export const HOME_COUNTRY = 'FR';

/** Flag emoji of an ISO 3166-1 alpha-2 code ('ES' → 🇪🇸); '' for anything else. */
export function flagOf(country: string | null | undefined): string {
  if (!country || !/^[A-Z]{2}$/.test(country)) return '';
  return String.fromCodePoint(...[...country].map((c) => 0x1f1e6 + c.charCodeAt(0) - 65));
}

/** A zone's chip label: its name, with its flag when it is abroad. */
function zoneLabel(zone: { name: Localized; country?: string | null }): Localized {
  const country = zone.country ?? HOME_COUNTRY;
  if (country === HOME_COUNTRY) return zone.name;
  const flag = flagOf(country);
  return { fr: `${flag} ${zone.name.fr}`, en: `${flag} ${zone.name.en}` };
}

const chip = (level: number, id: string, name: Localized, pressed: boolean): FilterChip => ({
  key: `${level}:${id}`,
  id,
  level,
  name,
  pressed,
});

/**
 * What the massif bar and the rankings show for a place path. `fallback` is
 * the massif kept on the page when no massif is chosen (the last one).
 */
export function geoState(
  path: string[],
  massifs: Massif[],
  stations: SiteStation[],
  domains: SiteDomain[],
  fallback: string,
): GeoState {
  const massif = massifs.find((m) => m.id === path[0]);
  if (!massif) {
    return {
      path: [],
      chips: massifs.map((m) => chip(1, m.id, m.name, false)),
      massifId: massifs.some((m) => m.id === fallback) ? fallback : (massifs[0]?.id ?? ''),
      stationIds: null,
    };
  }
  const kept = [massif.id];
  const chips = [chip(1, massif.id, massif.name, true)];
  const done = (stationIds: Set<string> | null): GeoState => ({
    path: kept,
    chips,
    massifId: massif.id,
    stationIds,
  });
  const ofMassif = stations.filter((s) => s.massifId === massif.id);

  // Level 2: zones with stations (skipped below two).
  let inZone = ofMassif;
  let zoneChosen = false;
  const isHome = (z: { country?: string | null }) => (z.country ?? HOME_COUNTRY) === HOME_COUNTRY;
  const withStations = (massif.zones ?? []).filter((z) => ofMassif.some((s) => s.zone === z.id));
  // One mixed list: the French départements first, then the foreign regions.
  const zones = [...withStations.filter(isHome), ...withStations.filter((z) => !isHome(z))];
  if (zones.length >= 2) {
    const zone = zones.find((z) => z.id === path[kept.length]);
    const level = kept.length + 1;
    if (!zone) {
      chips.push(...zones.map((z) => chip(level, z.id, zoneLabel(z), false)));
      return done(null);
    }
    kept.push(zone.id);
    chips.push(chip(level, zone.id, zoneLabel(zone), true));
    inZone = ofMassif.filter((s) => s.zone === zone.id);
    zoneChosen = true;
  }

  // Level 3: linked areas with at least two stations, one of them in the zone.
  const members = (domainId: string) => ofMassif.filter((s) => s.domain === domainId);
  const areas = domains.filter(
    (d) =>
      d.massifId === massif.id &&
      members(d.id).length >= 2 &&
      inZone.some((s) => s.domain === d.id),
  );
  const inZoneIds = zoneChosen ? new Set(inZone.map((s) => s.id)) : null;
  if (areas.length === 0) return done(inZoneIds);
  const area = areas.find((d) => d.id === path[kept.length]);
  const level = kept.length + 1;
  const label = (name: string): Localized => ({ fr: name, en: name });
  if (!area) {
    chips.push(...areas.map((d) => chip(level, d.id, label(d.name), false)));
    return done(inZoneIds);
  }
  kept.push(area.id);
  chips.push(chip(level, area.id, label(area.name), true));
  return done(new Set(members(area.id).map((s) => s.id)));
}

/** The place path stored in the preferences (`pyrenees/hautes-pyrenees`). */
export function readGeoPath(stored: string | null, legacyMassif: string | null): string[] {
  if (stored) return stored.split('/').filter(Boolean);
  return legacyMassif ? [legacyMassif] : [];
}
