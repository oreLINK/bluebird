/**
 * Reactive appearance store: `theme.choice` re-renders the header button when
 * it changes; `theme.set()` applies and remembers it (lib/theme.ts).
 */
import { readPref, writePref } from './prefs';
import { type ThemeChoice, applyTheme, parseTheme } from './theme';

function metas(): HTMLMetaElement[] {
  return [...document.querySelectorAll<HTMLMetaElement>('meta[name="theme-color"]')];
}

class Theme {
  choice = $state<ThemeChoice>(parseTheme(readPref('theme')));

  constructor() {
    if (typeof document !== 'undefined') applyTheme(this.choice, document.documentElement, metas());
  }

  set(choice: ThemeChoice): void {
    this.choice = choice;
    writePref('theme', choice);
    applyTheme(choice, document.documentElement, metas());
  }
}

export const theme = new Theme();
