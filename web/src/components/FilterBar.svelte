<!--
  Filter bar under the header (config/filters.yaml): one chip per filter in a
  horizontally scrollable row (touch swipe, trackpad, or mouse wheel on
  desktop). Edges fade when more chips are hidden on that side, and the
  selected chip is scrolled into view.
-->
<script lang="ts">
  import type { Filter } from '../lib/config';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import Icon from './Icon.svelte';

  let {
    filters,
    selected,
    onselect,
  }: { filters: Filter[]; selected: string; onselect: (id: string) => void } = $props();

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
    void filters.length;
    updateFades();
  });
</script>

<svelte:window onresize={updateFades} />

<nav
  bind:this={bar}
  class="bar"
  class:fade-start={fadeStart}
  class:fade-end={fadeEnd}
  aria-label={i18n.t('filters.label')}
  onscroll={updateFades}
  {onwheel}
>
  {#each filters as filter (filter.id)}
    <button
      type="button"
      class="chip"
      aria-pressed={filter.id === selected}
      onclick={(event) => choose(filter.id, event.currentTarget)}
    >
      {#if filter.icon}<Icon name={filter.icon} size={18} />{/if}
      <span>{i18n.pick(filter.name)}</span>
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
</style>
