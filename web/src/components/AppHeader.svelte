<!--
  Sticky app bar on frosted glass: logo on the left; on the right, the
  appearance button (icon of the current choice: system, light, dark; opens
  ThemePicker.svelte) then the flag of the current language (opens
  LanguagePicker.svelte), same look; below, the massif bar
  (place levels of lib/geoLevels.ts: massif, département, linked area), then
  the filter bar (filter levels of lib/filterLevels.ts), both with the same
  chips.

  Compact mode (lib/compactHeader.ts): while the page scrolls down, the two
  chip bars fold away and one row recalls the chosen place and the chosen
  filter (two pills at most); scrolling up, or tapping that row, opens the
  bars again. Logo and language button never move. Both rows fold and unfold
  with a height + fade transition (instant with reduced motion).
-->
<script lang="ts">
  import { tick } from 'svelte';
  import { SCROLL_OPTIONS, type ScrollState, headerSummary, nextScrollState } from '../lib/compactHeader';
  import type { FilterChip } from '../lib/filterLevels';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import FilterBar from './FilterBar.svelte';
  import { LOCALE_FLAGS, LOCALE_NAMES } from '../lib/i18n/core';
  import { THEME_ICONS } from '../lib/theme';
  import { theme } from '../lib/theme.svelte';
  import Flag from './Flag.svelte';
  import Icon from './Icon.svelte';
  import Logo from './Logo.svelte';

  let {
    places,
    onselectplace,
    filters,
    onselectfilter,
    languageOpen,
    onlanguage,
    themeOpen,
    ontheme,
  }: {
    places: FilterChip[];
    /** Called with the chip `key`. */
    onselectplace: (key: string) => void;
    filters: FilterChip[];
    /** Called with the chip `key`. */
    onselectfilter: (key: string) => void;
    languageOpen: boolean;
    onlanguage: () => void;
    themeOpen: boolean;
    ontheme: () => void;
  } = $props();

  const THEME_LABELS = { system: 'theme.system', light: 'theme.light', dark: 'theme.dark' } as const;

  const uid = $props.id();

  /** The chip bars are folded (page scrolled down). */
  let collapsed = $state(false);
  let barsEl = $state<HTMLElement>();

  const summary = $derived(headerSummary(places, filters));
  const filterText = $derived(summary.filter.map((c) => i18n.pick(c.name)).join(' · '));
  const filterIcon = $derived(summary.filter[0]?.icon ?? null);
  const filterRewind = $derived(summary.filter[0]?.theme === 'rewind');
  const filterMood = $derived(summary.filter[0]?.theme === 'mood');

  /** While the bars fold or unfold, the page height changes: ignore scroll events. */
  const SETTLE_MS = 420;
  let scroll: ScrollState = { collapsed: false, anchor: 0 };
  let settleUntil = 0;

  function setCollapsed(value: boolean) {
    collapsed = value;
    scroll = { collapsed: value, anchor: window.scrollY };
    settleUntil = performance.now() + SETTLE_MS;
  }

  $effect(() => {
    scroll = { collapsed: false, anchor: window.scrollY };
    let frame = 0;
    const onScroll = () => {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        const y = window.scrollY;
        if (performance.now() < settleUntil) {
          scroll = { ...scroll, anchor: y };
          return;
        }
        // Never fold the bars under a keyboard user's focus. A chip tapped with
        // a finger or a mouse keeps the focus too, but not `:focus-visible`:
        // that one must not block folding.
        if (!scroll.collapsed && keyboardFocusIn(barsEl)) {
          scroll = { ...scroll, anchor: Math.min(scroll.anchor, y) };
          return;
        }
        const next = nextScrollState(scroll, y, SCROLL_OPTIONS);
        if (next.collapsed !== scroll.collapsed) setCollapsed(next.collapsed);
        else scroll = next;
      });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      cancelAnimationFrame(frame);
    };
  });

  function keyboardFocusIn(element: HTMLElement | undefined): boolean {
    const active = document.activeElement;
    return !!element && !!active && element.contains(active) && active.matches(':focus-visible');
  }

  async function expand(event: MouseEvent) {
    setCollapsed(false);
    // Keyboard activation (Enter / Space: no pointer, detail 0): the summary
    // button becomes inert, so move the focus to the chosen chip.
    if (event.detail !== 0) return;
    await tick();
    barsEl?.querySelector<HTMLElement>('button[aria-pressed="true"], button')?.focus({ preventScroll: true });
  }
</script>

<header class="header glass" class:collapsed>
  <div class="container inner">
    <div class="top">
      <h1 class="brand"><Logo /></h1>
      <div class="actions">
        <button
          type="button"
          class="header-button"
          aria-label={i18n.t('theme.open', { theme: i18n.t(THEME_LABELS[theme.choice]) })}
          aria-haspopup="dialog"
          aria-expanded={themeOpen}
          onclick={ontheme}
        >
          <Icon name={THEME_ICONS[theme.choice]} size={22} />
        </button>
        <button
          type="button"
          class="header-button"
          aria-label={i18n.t('language.open', { language: LOCALE_NAMES[i18n.locale] })}
          aria-haspopup="dialog"
          aria-expanded={languageOpen}
          onclick={onlanguage}
        >
          <Flag country={LOCALE_FLAGS[i18n.locale]} width={26} />
        </button>
      </div>
    </div>

    <div class="fold" class:closed={collapsed} inert={collapsed} id="{uid}-bars">
      <div class="clip">
        <div class="bars" bind:this={barsEl}>
          {#if places.length > 0}
            <FilterBar
              options={places.map((c) => ({ ...c, removable: c.pressed }))}
              onselect={onselectplace}
              resetScroll
              label={i18n.t('massifs.label')}
            />
          {/if}
          {#if filters.length > 0}
            <FilterBar
              options={filters.map((c) => ({ ...c, removable: c.pressed }))}
              onselect={onselectfilter}
              resetScroll
              label={i18n.t('filters.label')}
            />
          {/if}
        </div>
      </div>
    </div>

    <div class="fold summary-fold" class:closed={!collapsed} inert={!collapsed}>
      <div class="clip">
        <div class="summary-row">
          <button
            type="button"
            class="summary"
            aria-controls="{uid}-bars"
            aria-expanded="false"
            aria-label={i18n.t('header.showFilters')}
            onclick={expand}
          >
            {#if summary.place}
              <span class="pill place"><span class="pill-text">{i18n.pick(summary.place.name)}</span></span>
            {/if}
            {#if summary.filter.length > 0}
              <span class="pill" class:rewind={filterRewind} class:mood={filterMood}>
                {#if filterIcon}<Icon name={filterIcon} size={15} />{/if}
                <span class="pill-text">{filterText}</span>
              </span>
            {/if}
            <Icon name="chevron" size={16} class="more" />
          </button>
        </div>
      </div>
    </div>
  </div>
</header>

<style>
  .header {
    position: sticky;
    top: 0;
    z-index: 10;
    padding-top: env(safe-area-inset-top);
  }

  .inner {
    display: grid;
    padding-top: 10px;
    padding-bottom: 10px;
  }

  .top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .brand {
    display: flex;
    min-width: 0;
  }

  .actions {
    display: flex;
    flex: none;
    gap: 8px;
  }

  .header-button {
    display: grid;
    place-items: center;
    flex: none;
    width: 44px;
    height: 44px;
    border-radius: var(--radius-s);
    border: 1px solid var(--line);
    background: var(--surface);
    color: var(--brand);
    cursor: pointer;
  }

  /*
   * A row that folds: its grid track goes from 1fr to 0fr while it fades and
   * rises a little, so the header shrinks smoothly. The two folds cross-fade.
   */
  .fold {
    display: grid;
    /* minmax(0, …): long nowrap pills must shrink, not widen the header. */
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: 1fr;
    opacity: 1;
    transform: none;
    transition:
      grid-template-rows 0.36s cubic-bezier(0.2, 0.7, 0.2, 1),
      opacity 0.26s ease 0.06s,
      transform 0.36s cubic-bezier(0.2, 0.7, 0.2, 1);
  }

  .fold.closed {
    grid-template-rows: 0fr;
    opacity: 0;
    transform: translateY(-6px);
    transition:
      grid-template-rows 0.36s cubic-bezier(0.2, 0.7, 0.2, 1),
      opacity 0.18s ease,
      transform 0.36s cubic-bezier(0.2, 0.7, 0.2, 1);
  }

  .clip {
    min-width: 0;
    min-height: 0;
    /* Clip the height only: the chip bars bleed to the screen edges. */
    overflow-x: visible;
    overflow-y: clip;
  }

  .bars {
    display: grid;
    gap: 6px;
    padding-top: 10px;
  }

  .summary-row {
    padding-top: 8px;
  }

  /* Folded: one line only, two pills at most, each shortened with an ellipsis. */
  .summary {
    display: flex;
    flex-wrap: nowrap;
    align-items: center;
    gap: 6px;
    width: 100%;
    min-width: 0;
    padding: 0;
    border: 0;
    background: none;
    text-align: left;
    cursor: pointer;
  }

  .pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    flex: 0 1 auto;
    min-width: 0;
    min-height: 2.125rem;
    padding: 0 12px;
    border-radius: 999px;
    border: 1px solid var(--brand);
    background: var(--brand);
    color: var(--on-brand);
    font-size: 0.8125rem;
    font-weight: 600;
    white-space: nowrap;
  }

  /* When both are too long, the filter pill gives way first. */
  .pill.place {
    flex-shrink: 1;
    max-width: 60%;
  }

  .pill:not(.place) {
    flex-shrink: 4;
  }

  .pill :global(svg) {
    flex: none;
  }

  .pill-text {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .pill.rewind {
    border-color: var(--rewind-red);
    background: var(--rewind-red);
    color: var(--on-rewind);
  }

  /* Mood filter: filled like its chosen chip (FilterBar), colours sliding left to right. */
  .pill.mood {
    border-color: transparent;
    background: linear-gradient(
      90deg,
      var(--mood-fill-1),
      var(--mood-fill-2),
      var(--mood-fill-3),
      var(--mood-fill-4),
      var(--mood-fill-5),
      var(--mood-fill-1),
      var(--mood-fill-2),
      var(--mood-fill-3),
      var(--mood-fill-4),
      var(--mood-fill-5),
      var(--mood-fill-1)
    );
    background-size: 200% 100%;
    color: var(--on-mood);
    animation: pill-mood 4s linear infinite;
  }

  @keyframes pill-mood {
    from {
      background-position: 100% 0;
    }
    to {
      background-position: 0% 0;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .pill.mood {
      animation: none;
    }
  }

  .summary :global(.more) {
    flex: none;
    margin-left: auto;
    color: var(--ink-faint);
  }

  .summary:focus-visible {
    outline: 3px solid var(--focus);
    outline-offset: 3px;
    border-radius: 999px;
  }
</style>
