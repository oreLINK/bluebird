import { describe, expect, it } from 'vitest';
import { type FontLoader, splitSignTitle, titleFontReady } from './titleStyles';

const fonts = (load: FontLoader['load']): FontLoader => ({ load });

describe('the two lines of a danger sign', () => {
  it('splits after the apostrophe, else before the last word, keeping the space', () => {
    expect(splitSignTitle("Risque d'avalanche")).toEqual(["Risque d'", 'avalanche']);
    expect(splitSignTitle('Risque d’avalanche')).toEqual(['Risque d’', 'avalanche']);
    expect(splitSignTitle('Avalanche danger')).toEqual(['Avalanche ', 'danger']);
    expect(splitSignTitle('Peligro de aludes')).toEqual(['Peligro de ', 'aludes']);
    expect(splitSignTitle('Avalanche')).toEqual(['', 'Avalanche']);
  });

  it('reads whole once the lines are joined', () => {
    for (const title of ["Risque d'avalanche", 'Avalanche danger', 'Peligro de aludes']) {
      expect(splitSignTitle(title).join('')).toBe(title);
    }
  });
});

describe('styled titles wait for their font', () => {
  it('asks for the face of the style and is ready once it has loaded', async () => {
    const asked: string[] = [];
    const ready = await titleFontReady('sunrise', 'Bluebird', fonts(async (font) => {
      asked.push(font);
      return [{}];
    }));
    expect(ready).toBe(true);
    expect(asked).toEqual(['400 1em "Righteous"']);
  });

  it('keeps the standard title when no face matches or the load fails', async () => {
    expect(await titleFontReady('sunrise', 'Bluebird', fonts(async () => []))).toBe(false);
    expect(await titleFontReady('sunrise', 'Bluebird', fonts(() => Promise.reject(new Error('offline'))))).toBe(false);
  });

  it('gives up after the timeout on a slow network', async () => {
    const never = fonts(() => new Promise(() => {}));
    expect(await titleFontReady('sunrise', 'Bluebird', never, 20)).toBe(false);
  });

  it('keeps the standard title without a font loading API', async () => {
    expect(await titleFontReady('sunrise', 'Bluebird', {} as FontLoader)).toBe(false);
  });
});
