/* Generated from config/schemas/stations.schema.json by `npm run gen:types`. Do not edit. */

export type GroomingEnd = string;
export type LiftsOpen = string;
export type Id = string;
export type Name = string;
export type Domains = Domain[];
export type Id1 = string;
export type Name1 = string;
/**
 * Compact name displayed in the tiles; defaults to `name`.
 */
export type ShortName = string | null;
export type Lat = number;
export type Lon = number;
export type Base = number;
export type Summit = number;
/**
 * Defaults to the base/summit average.
 */
export type Mid = number | null;
/**
 * Dominant slope aspects.
 */
export type Aspects = ('N' | 'NE' | 'E' | 'SE' | 'S' | 'SW' | 'W' | 'NW')[];
/**
 * Overrides the default.
 */
export type GroomingEnd1 = string | null;
/**
 * Overrides the default.
 */
export type LiftsOpen1 = string | null;
export type Website = string | null;
export type Enabled = boolean;
/**
 * Sub-massif of the station (`zones` of config/massifs.yaml).
 */
export type Zone = string | null;
/**
 * Linked ski area it belongs to (`domains` of its file).
 */
export type Domain1 = string | null;
export type Stations = Station[];

/**
 * Schema of ``config/stations/<massif>.yaml``.
 */
export interface StationsFile {
  defaults?: StationDefaults;
  domains?: Domains;
  stations: Stations;
}
/**
 * Values applied to every station of the file unless it overrides them.
 */
export interface StationDefaults {
  grooming_end?: GroomingEnd;
  lifts_open?: LiftsOpen;
}
/**
 * A linked ski area spanning several stations (Les 3 Vallées, Portes du Soleil…),
 * level 3 of the massif bar; its stations may sit in several zones or countries.
 */
export interface Domain {
  id: Id;
  name: Name;
}
/**
 * A ski resort.
 */
export interface Station {
  id: Id1;
  name: Name1;
  short_name?: ShortName;
  lat: Lat;
  lon: Lon;
  elevation: Elevation;
  aspects?: Aspects;
  grooming_end?: GroomingEnd1;
  lifts_open?: LiftsOpen1;
  website?: Website;
  enabled?: Enabled;
  zone?: Zone;
  domain?: Domain1;
}
/**
 * Elevations of a ski area, in metres.
 */
export interface Elevation {
  base: Base;
  summit: Summit;
  mid?: Mid;
}
