/* Generated from config/schemas/sources.schema.json by `npm run gen:types`. Do not edit. */

export type Id = string;
export type Extractor = string;
export type Transformer = string;
export type Enabled = boolean;
export type Schedule = 'daily' | 'on_demand';
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
 * Credit displayed in the site footer.
 */
export interface Attribution {
  name: Name;
  url: Url;
  license?: License;
}
