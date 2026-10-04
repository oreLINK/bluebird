/* Generated from config/schemas/sources.schema.json by `npm run gen:types`. Do not edit. */

export type Id = string;
export type Extractor = string;
export type Transformer = string;
export type Enabled = boolean;
/**
 * daily: fetched by every refresh; on_demand: only with `bluebird run --source`; reference: slow-changing data refreshed with `bluebird reference` and committed under config/reference/; season: archive of a closed season, fetched once by `bluebird rewind` and committed under config/rewind/.
 */
export type Schedule = 'daily' | 'on_demand' | 'reference' | 'season';
export type Name = string;
export type Url = string;
export type License = string | null;
export type Sources = Source[];

/**
 * Schema of ``config/sources.yaml``.
 */
export interface SourcesFile {
  sources: Sources;
}
/**
 * A data source: a bronze Extractor paired with a silver Transformer.
 */
export interface Source {
  id: Id;
  extractor: Extractor;
  transformer: Transformer;
  enabled?: Enabled;
  schedule?: Schedule;
  params?: Params;
  attribution: Attribution;
}
export interface Params {
  [k: string]: unknown;
}
/**
 * Credit displayed on the tile backs and on the "about" page (config/pages.yaml).
 */
export interface Attribution {
  name: Name;
  url: Url;
  license?: License;
}
