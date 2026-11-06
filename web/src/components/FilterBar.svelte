<!--
  A horizontally scrollable row of choices in the header (touch swipe,
  trackpad, or mouse wheel on desktop). Edges fade when more choices are
  hidden on that side, and the selected one is scrolled into view.
  Used twice by AppHeader, with the same chips, Spotify-style levels: the
  massif bar (places, lib/geoLevels.ts) and the filter bar
  (lib/filterLevels.ts). Chosen chips are filled with a × (`removable`) and
  lead the row; the bar scrolls back to its start after each choice, as far
  as the last chosen chip stays visible (`resetScroll`). Chips arriving grow
  in; the others slide to their new place (reduced-motion aware).
-->
<script lang="ts" module>
  import type { Filter } from '../lib/config';

  /** A choice of the bar: a filter chip, or a massif (no icon). */
  export interface BarOption {
    id: string;
    /** Unique key in the bar when ids can repeat (filter levels); defaults to `id`. */
    key?: string;
    /** Selected: filled chip, `aria-pressed`. */
    pressed: boolean;
    /** A pressed chip with a ×: tapping it removes the choice. */
    removable?: boolean;
    name: Filter['name'];
    icon?: string | null;
    /** `rewind`: Christmas-red chip; `mood`: moving multicolour text and border (config/filters.yaml `theme`). */
    theme?: Filter['theme'];
  }
</script>

<script lang="ts">
  import { tick } from 'svelte';
  import { flip } from 'svelte/animate';
  import { cubicOut } from 'svelte/easing';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { motion } from '../lib/transitions';
  import Icon from './Icon.svelte';

  let {
    options,
    onselect,
    label,
    resetScroll = false,
  }: {
    options: BarOption[];
    /** Called with the option `key` (or `id`). */
    onselect: (key: string) => void;
    label: string;
    /** Scroll back to the start after a choice (chosen chips lead the row). */
    resetScroll?: boolean;
  } = $props();

  const keyOf = (option: BarOption) => option.key ?? option.id;

  /** A chip appearing: grows in while fading in. */
  function grow(_node: Element) {
    return {
      duration: motion(200),
      easing: cubicOut,
      css: (t: number) => `opacity: ${t}; transform: scale(${0.85 + 0.15 * t});`,
    };
  }

  let bar = $state<HTMLElement>();
  let fadeStart = $state(false);
  let fadeEnd = $state(false);

  function updateFades() {
    if (!bar) return;
    fadeStart = bar.scrollLeft > 2;
    fadeEnd = bar.scrollLeft + bar.clientWidth < bar.scrollWidth - 2;
  }

  /** Mouse wheels scroll vertically: turn that into horizontal scrolling here. */
  function onwheel(event: WheelEvent) {
    if (!bar || bar.scrollWidth <= bar.clientWidth) return;
    if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;
    event.preventDefault();
    bar.scrollLeft += event.deltaY;
  }

  async function choose(option: BarOption, button: HTMLElement) {
    onselect(keyOf(option));
    if (!resetScroll) {
      button.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
      return;
    }
    await tick(); // the chips of the new level are in place
    if (!bar) return;
    // Back to the start, unless the last chosen chip would then be hidden (deep levels).
    const chosen = [...bar.querySelectorAll<HTMLElement>('.chip[aria-pressed="true"]')].at(-1);
    const end = chosen ? chosen.offsetLeft + chosen.offsetWidth - bar.offsetLeft : 0;
    const left = Math.max(0, end - bar.clientWidth + 24);
    bar.scrollTo({ left, behavior: motion(1) ? 'smooth' : 'instant' });
  }

  $effect(() => {
    void options.length;
    updateFades();
  });
</script>

<svelte:window onresize={updateFades} />

<nav
  bind:this={bar}
  class="bar"
  class:fade-start={fadeStart}
  class:fade-end={fadeEnd}
  aria-label={label}
  onscroll={updateFades}
  {onwheel}
>
  {#each options as option (keyOf(option))}
    <button
      type="button"
      class="chip"
      class:rewind={option.theme === 'rewind'}
      class:mood={option.theme === 'mood'}
      class:removable={option.removable}
      aria-pressed={option.pressed}
      aria-label={option.removable
        ? i18n.t('filters.remove', { name: i18n.pick(option.name) })
        : undefined}
      onclick={(event) => choose(option, event.currentTarget)}
      animate:flip={{ duration: motion(220), easing: cubicOut }}
      in:grow
    >
      {#if option.icon}<Icon name={option.icon} size={16} />{/if}
      <span>{i18n.pick(option.name)}</span>
      {#if option.removable}<Icon name="close" size={14} class="remove" />{/if}
    </button>
  {/each}
</nav>

<style>
  .bar {
    --fade: 28px;
    display: flex;
    gap: 6px;
    overflow-x: auto;
    overscroll-behavior-x: contain;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    scroll-snap-type: x proximity;
    scroll-padding-inline: var(--gutter);
    margin: 0 calc(-1 * var(--gutter));
    padding: 2px var(--gutter);
  }

  .bar::-webkit-scrollbar {
    display: none;
  }

  .fade-start {
    -webkit-mask-image: linear-gradient(90deg, transparent, #000 var(--fade));
    mask-image: linear-gradient(90deg, transparent, #000 var(--fade));
  }

  .fade-end {
    -webkit-mask-image: linear-gradient(90deg, #000 calc(100% - var(--fade)), transparent);
    mask-image: linear-gradient(90deg, #000 calc(100% - var(--fade)), transparent);
  }

  .fade-start.fade-end {
    -webkit-mask-image: linear-gradient(
      90deg,
      transparent,
      #000 var(--fade),
      #000 calc(100% - var(--fade)),
      transparent
    );
    mask-image: linear-gradient(
      90deg,
      transparent,
      #000 var(--fade),
      #000 calc(100% - var(--fade)),
      transparent
    );
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    flex: none;
    scroll-snap-align: start;
    min-height: 2.125rem;
    padding: 0 12px 0 10px;
    border-radius: 999px;
    /* Glass chip (design "Nuit étoilée"). */
    border: 1px solid var(--line);
    background: color-mix(in srgb, var(--surface) 75%, transparent);
    box-shadow: inset 0 1px 0 var(--glass-hi);
    color: var(--ink-soft);
    font-size: 0.8125rem;
    font-weight: 600;
    white-space: nowrap;
    cursor: pointer;
  }

  .chip :global(svg) {
    color: var(--prob-high);
  }

  .chip[aria-pressed='true'] {
    border-color: var(--brand);
    background: var(--brand);
    box-shadow: none;
    color: var(--on-brand);
  }

  .chip[aria-pressed='true'] :global(svg) {
    color: inherit;
  }

  /* Rewind filter: red outline and text, filled red when selected. */
  .chip.rewind {
    border-color: var(--rewind-red);
    color: var(--rewind-ink);
  }

  .chip.rewind :global(svg) {
    color: var(--rewind-ink);
  }

  .chip.rewind[aria-pressed='true'] {
    background: var(--rewind-red);
    color: var(--on-rewind);
  }

  .chip.rewind[aria-pressed='true'] :global(svg) {
    color: inherit;
  }

  /*
   * Mood filter: text and border slide through the --mood-* colours from left
   * to right, so the chip is easy to spot; filled with the darker
   * --mood-fill-* and white text when chosen. The gradient repeats once over
   * 200 % of the chip, so moving it by one chip width loops seamlessly.
   * Static with reduced motion. The page background stays plain (invariant 14).
   */
  .chip.mood {
    --mood-band: linear-gradient(
      90deg,
      var(--mood-1),
      var(--mood-2),
      var(--mood-3),
      var(--mood-4),
      var(--mood-5),
      var(--mood-1),
      var(--mood-2),
      var(--mood-3),
      var(--mood-4),
      var(--mood-5),
      var(--mood-1)
    );
    border-color: transparent;
    background:
      linear-gradient(var(--surface), var(--surface)) padding-box,
      var(--mood-band) border-box;
    background-size:
      100% 100%,
      200% 100%;
    animation: mood-slide 4s linear infinite;
  }

  .chip.mood span {
    background: var(--mood-band);
    background-size: 200% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: mood-text 4s linear infinite;
  }

  .chip.mood :global(svg) {
    animation: mood-icon 4s linear infinite;
  }

  .chip.mood[aria-pressed='true'] {
    --mood-band: linear-gradient(
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
    background: var(--mood-band);
    background-size: 200% 100%;
    color: var(--on-mood);
    animation: mood-text 4s linear infinite;
  }

  .chip.mood[aria-pressed='true'] span {
    background: none;
    color: inherit;
    animation: none;
  }

  .chip.mood[aria-pressed='true'] :global(svg) {
    color: inherit;
    animation: none;
  }

  /* Left to right: the image starts one chip width to the left and slides right. */
  @keyframes mood-slide {
    from {
      background-position:
        0 0,
        100% 0;
    }
    to {
      background-position:
        0 0,
        0% 0;
    }
  }

  @keyframes mood-text {
    from {
      background-position: 100% 0;
    }
    to {
      background-position: 0% 0;
    }
  }

  @keyframes mood-icon {
    0%,
    100% {
      color: var(--mood-1);
    }
    20% {
      color: var(--mood-2);
    }
    40% {
      color: var(--mood-3);
    }
    60% {
      color: var(--mood-4);
    }
    80% {
      color: var(--mood-5);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .chip.mood,
    .chip.mood span,
    .chip.mood :global(svg) {
      animation: none;
    }

    .chip.mood :global(svg) {
      color: var(--mood-1);
    }
  }

  /* Chosen filter: the × after the text says a tap removes it. */
  .chip.removable {
    padding-right: 10px;
  }

  .chip :global(.remove) {
    margin-left: 1px;
    stroke-width: 2.4;
  }
</style>
