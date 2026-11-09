/**
 * Styled titles of `full` tiles (tile `title_style` in config/tiles.yaml,
 * TILES.md §3): a WordArt-like title proper to one KPI, in a free
 * self-hosted font. The tile shows its standard title until the style's font
 * face has loaded, and keeps it if the face never loads (slow or no network,
 * blocked font, old browser): the styled title is a bonus, never a condition.
 */
import type { TitleStyle } from './generated/tiles';

export type StyleId = Exclude<TitleStyle, null>;

/** The font face each style needs (a CSS `font` shorthand for `FontFaceSet.load`). */
export const TITLE_STYLES: Record<StyleId, { font: string }> = {
  sunrise: { font: '400 1em "Righteous"' },
  danger_sign: { font: '700 1em "Oswald"' },
};

/**
 * The two lines of a danger sign: a small upper line and a large lower one
 * ("Risque d'" / "avalanche", "Avalanche " / "danger", "Peligro de " /
 * "aludes"). Splits after the last apostrophe, else before the last word. The
 * space stays at the end of the first line, so the text still reads whole
 * ("Avalanche danger") for screen readers and copy.
 */
export function splitSignTitle(text: string): [string, string] {
  const words = text.trim();
  const apostrophe = Math.max(words.lastIndexOf("'"), words.lastIndexOf('’'));
  if (apostrophe > 0 && apostrophe < words.length - 1) {
    return [words.slice(0, apostrophe + 1), words.slice(apostrophe + 1)];
  }
  const space = words.lastIndexOf(' ');
  if (space > 0) return [words.slice(0, space + 1), words.slice(space + 1)];
  return ['', words];
}

/** How long a tile waits for the font before keeping its standard title. */
export const TITLE_FONT_TIMEOUT_MS = 3000;

/** The part of `document.fonts` this module uses (a fake in tests). */
export interface FontLoader {
  load(font: string, text?: string): Promise<unknown[]>;
}

/**
 * Whether the font of `style` is ready to draw `text`: true once the face has
 * loaded; false if it fails, finds no face, takes longer than `timeoutMs`, or
 * the browser has no font loading API.
 */
export async function titleFontReady(
  style: StyleId,
  text: string,
  fonts: FontLoader | undefined = globalThis.document?.fonts,
  timeoutMs = TITLE_FONT_TIMEOUT_MS,
): Promise<boolean> {
  if (!fonts || typeof fonts.load !== 'function') return false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<boolean>((resolve) => {
    timer = setTimeout(() => resolve(false), timeoutMs);
  });
  const loaded = fonts.load(TITLE_STYLES[style].font, text).then(
    (faces) => faces.length > 0,
    () => false,
  );
  try {
    return await Promise.race([loaded, timeout]);
  } finally {
    clearTimeout(timer);
  }
}
