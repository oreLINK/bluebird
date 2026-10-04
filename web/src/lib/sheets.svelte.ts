/**
 * Router of the full-window sheets (components/Sheet.svelte): which sheet is
 * open, kept in the URL hash (`#<id>`) so a sheet can be linked to, and so
 * the browser or phone "back" gesture closes it.
 *
 *   sheets.open('legal')   push `#legal` to the history and show the sheet
 *   sheets.close()         go back (or drop the hash when the page was opened
 *                          directly on `#legal`)
 *
 * Any component can show a sheet for an id: `open={sheets.current === id}`.
 * Config pages (config/pages.yaml) use it through InfoPage.svelte; other
 * kinds of sheets can reuse it with their own ids.
 */

/** Sheet id carried by a URL hash (`#legal` → `legal`), or null. */
export function sheetIdFromHash(hash: string): string | null {
  const id = hash.replace(/^#\/?/, '');
  return /^[a-z0-9]+(?:[_-][a-z0-9]+)*$/.test(id) ? id : null;
}

class SheetRouter {
  current = $state<string | null>(null);
  /** True when `current` was pushed by `open()`, so "back" returns to the page. */
  #pushed = false;

  constructor() {
    if (typeof window === 'undefined') return;
    this.current = sheetIdFromHash(window.location.hash);
    window.addEventListener('popstate', () => {
      this.current = sheetIdFromHash(window.location.hash);
      this.#pushed = false;
    });
  }

  open(id: string): void {
    if (this.current === id) return;
    history.pushState({ sheet: id }, '', `#${id}`);
    this.current = id;
    this.#pushed = true;
  }

  close(): void {
    if (this.current === null) return;
    this.current = null;
    if (this.#pushed) {
      this.#pushed = false;
      history.back();
    } else {
      history.replaceState(history.state, '', window.location.pathname + window.location.search);
    }
  }
}

export const sheets = new SheetRouter();
