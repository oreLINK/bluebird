import { describe, expect, it } from 'vitest';
import { sheetIdFromHash } from './sheets.svelte';

describe('sheetIdFromHash', () => {
  it('reads a sheet id from the URL hash', () => {
    expect(sheetIdFromHash('#legal')).toBe('legal');
    expect(sheetIdFromHash('#/privacy')).toBe('privacy');
  });

  it('ignores empty and malformed hashes', () => {
    expect(sheetIdFromHash('')).toBeNull();
    expect(sheetIdFromHash('#')).toBeNull();
    expect(sheetIdFromHash('#Not a page')).toBeNull();
  });
});
