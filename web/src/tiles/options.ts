/**
 * Read typed values from a tile's free-form `options` (config/tiles.yaml),
 * falling back to a default when the option is missing or has the wrong type.
 */
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
