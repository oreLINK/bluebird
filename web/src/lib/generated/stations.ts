/* Generated from config/schemas/stations.schema.json by `npm run gen:types`. Do not edit. */

export type GroomingEnd = string;
export type LiftsOpen = string;
export type Id = string;
export type Name = string;
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
export type Stations = Station[];

/**
 * Schema of ``config/stations/<massif>.yaml``.
 */
export interface StationsFile {
  defaults?: StationDefaults;
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
 * A ski resort.
 */
export interface Station {
  id: Id;
  name: Name;
  lat: Lat;
  lon: Lon;
  elevation: Elevation;
  aspects?: Aspects;
  grooming_end?: GroomingEnd1;
  lifts_open?: LiftsOpen1;
  website?: Website;
  enabled?: Enabled;
}
/**
 * Elevations of a ski area, in metres.
 */
export interface Elevation {
  base: Base;
  summit: Summit;
  mid?: Mid;
}
