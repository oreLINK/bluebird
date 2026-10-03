/* Generated from config/schemas/layout.schema.json by `npm run gen:types`. Do not edit. */

export type Default = string[];

/**
 * Schema of ``config/layout.yaml``: tile order, optionally per massif.
 */
export interface LayoutFile {
  default: Default;
  overrides?: Overrides;
}
export interface Overrides {
  [k: string]: string[];
}
