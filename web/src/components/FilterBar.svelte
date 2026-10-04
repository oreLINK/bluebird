<!--
  A horizontally scrollable row of choices in the header (touch swipe,
  trackpad, or mouse wheel on desktop). Edges fade when more choices are
  hidden on that side, and the selected one is scrolled into view.
  Used twice by AppHeader, with the same chip style in two sizes:
    size `large`  the massif bar (config/massifs.yaml); one massif is always
                  selected, there is no "all" choice.
    size `small`  the filter bar (config/filters.yaml).
-->
<script lang="ts" module>
  import type { Filter } from '../lib/config';

  /** A choice of the bar: a filter, or a massif (no icon). */
  export interface BarOption {
    id: string;
    name: Filter['name'];
    icon?: string | null;
    /** `rewind`: Christmas-red chip (config/filters.yaml `theme`). */
    theme?: Filter['theme'];
  }
</script>

<script lang="ts">
  import { i18n } from '../lib/i18n/i18n.svelte';
  import Icon from './Icon.svelte';

  let {
    options,
    selected,
    onselect,
    label,
    size = 'small',
  }: {
    options: BarOption[];
    selected: string;
    onselect: (id: string) => void;
    label: string;
    size?: 'large' | 'small';
  } = $props();

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

  function choose(id: string, button: HTMLElement) {
    onselect(id);
    button.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
  }

  $effect(() => {
    void options.length;
    updateFades();
  });
</script>

<svelte:window onresize={updateFades} />

<nav
  bind:this={bar}
  class="bar {size}"
  class:fade-start={fadeStart}
  class:fade-end={fadeEnd}
  aria-label={label}
  onscroll={updateFades}
  {onwheel}
>
  {#each options as option (option.id)}
    <button
      type="button"
      class="chip"
      class:rewind={option.theme === 'rewind'}
      aria-pressed={option.id === selected}
      onclick={(event) => choose(option.id, event.currentTarget)}
    >
      {#if option.icon}<Icon name={option.icon} size={size === 'small' ? 16 : 18} />{/if}
      <span>{i18n.pick(option.name)}</span>
    </button>
  {/each}
</nav>

<style>
  .bar {
    --fade: 28px;
    display: flex;
    gap: 8px;
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
    gap: 7px;
    flex: none;
    scroll-snap-align: start;
    min-height: 2.5rem;
    padding: 0 16px 0 12px;
    border-radius: 999px;
    border: 1px solid var(--line);
    background: var(--surface);
    color: var(--ink-soft);
    font-size: 0.9375rem;
    font-weight: 700;
    white-space: nowrap;
    cursor: pointer;
  }

  .chip :global(svg) {
    color: var(--prob-high);
  }

  .chip[aria-pressed='true'] {
    border-color: var(--brand);
    background: var(--brand);
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

  /* Massif bar: larger chips, the main choice of the page. */
  .large .chip {
    min-height: 2.75rem;
    padding: 0 20px;
    font-size: 1.0625rem;
  }

  /* Filter bar: smaller chips, secondary to the massif. */
  .small {
    gap: 6px;
  }

  .small .chip {
    gap: 5px;
    min-height: 2.125rem;
    padding: 0 12px 0 10px;
    font-size: 0.8125rem;
  }
</style>
