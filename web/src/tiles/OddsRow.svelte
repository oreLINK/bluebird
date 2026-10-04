<!--
  The best stations of a KPI as betting-style "odds buttons": name, value
  ("82 %" for live KPIs, "4,43 m" for historical ones, lib/kpiView.ts) and,
  for live KPIs, reliability dots (ConfidenceDots); a bar below each. `overlay` adapts the bars for a photo or illustration background
  (TileBannerFull).
  `compact`: shorter boxes (one line of name, smaller value) for the simple
  tiles, so two of them stack beside a banner tile.
  `details`: when true, each box is a button that shows the station details
  (tile option `details`); when false (the default for now) the boxes are
  static and a tap on them does nothing (not even a flip).
-->
<script lang="ts">
  import ConfidenceDots from '../components/ConfidenceDots.svelte';
  import { formatOdds } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { type KpiView, type RankItem, fullName, itemLabel, shortName } from '../lib/kpiView';
  import { itemSummary } from './summary';

  let {
    tileId,
    label,
    view,
    top,
    selected,
    onselect,
    showOdds = false,
    overlay = false,
    compact = false,
    details = false,
  }: {
    tileId: string;
    label: string;
    view: KpiView;
    top: RankItem[];
    selected: string | null;
    onselect: (stationId: string) => void;
    showOdds?: boolean;
    overlay?: boolean;
    compact?: boolean;
    details?: boolean;
  } = $props();

  const summary = (item: RankItem, index: number) =>
    itemSummary(view, item, index + 1, fullName(view, item.stationId), i18n);
</script>

{#snippet face(item: RankItem)}
  <span class="odd-name" aria-hidden="true">{shortName(view, item.stationId)}</span>
  <span class="odd-value tabular" aria-hidden="true">{itemLabel(view, item, i18n.locale)}</span>
  {#if item.confidence}
    <ConfidenceDots level={item.confidence} size={5} />
  {:else}
    <span class="odd-gap" aria-hidden="true"></span>
  {/if}
  {#if showOdds}
    <span class="odd-odds tabular" aria-hidden="true">
      {i18n.t('tile.odds', { odds: formatOdds(item.value, i18n.locale) })}
    </span>
  {/if}
{/snippet}

<div class="odds" class:overlay class:compact role="group" aria-label={label} style="--n: {top.length}">
  {#each top as item, index (item.stationId)}
    <div class="odd">
      {#if details && item.entry}
        <button
          type="button"
          class="odd-button"
          aria-pressed={selected === item.stationId}
          aria-controls="{tileId}-top-details"
          aria-label={summary(item, index)}
          onclick={() => onselect(item.stationId)}
        >
          {@render face(item)}
        </button>
      {:else}
        <div class="odd-button static" data-no-flip>
          <span class="visually-hidden">{summary(item, index)}</span>
          {@render face(item)}
        </div>
      {/if}
      <span class="odd-bar" aria-hidden="true"><span style="--p: {item.share}"></span></span>
    </div>
  {/each}
</div>

<style>
  .odds {
    display: grid;
    grid-template-columns: repeat(var(--n, 3), minmax(0, 1fr));
    gap: 8px;
    padding-top: 6px;
  }

  .odd {
    display: grid;
    gap: 7px;
    min-width: 0;
  }

  .odd-button {
    position: relative;
    display: grid;
    /* Fixed size: two lines of name (2 × 0.75rem × 1.2), the percentage and the dots. */
    grid-template-rows: 1.8rem auto auto;
    justify-items: center;
    align-items: center;
    gap: 3px;
    height: var(--odds-button-h);
    padding: 10px 6px 8px;
    border-radius: var(--radius-m);
    border: 1px solid var(--pill-border);
    background: var(--pill-bg);
    color: var(--pill-ink);
    text-align: center;
    cursor: pointer;
    /* Empty reliability dots in the ink colour, so they show on the light-blue button. */
    --dot-off: color-mix(in oklch, currentColor 22%, transparent);
    transition:
      background 0.15s ease,
      color 0.15s ease;
  }

  .odd-button.static {
    cursor: default;
  }

  .odd-button[aria-pressed='true'] {
    --dot-on: currentColor;
    background: var(--pill-active-bg);
    border-color: var(--pill-active-bg);
    color: var(--pill-active-ink);
  }

  .overlay .odd-button {
    box-shadow: 0 6px 16px -8px rgba(0, 0, 0, 0.6);
  }

  .odd-name {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    overflow: hidden;
    font-size: 0.75rem;
    font-weight: 600;
    line-height: 1.2;
    overflow-wrap: anywhere;
  }

  .odd-gap {
    height: 5px;
  }

  .odd-value {
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-style: italic;
    font-weight: 800;
    line-height: 1.05;
  }

  .compact {
    padding-top: 2px;
  }

  .compact .odd {
    gap: 6px;
  }

  .compact .odd-button {
    grid-template-rows: 0.825rem auto auto;
    gap: 2px;
    height: var(--odds-button-compact-h);
    padding: 6px 6px 5px;
  }

  .compact .odd-name {
    -webkit-line-clamp: 1;
    line-clamp: 1;
    font-size: 0.6875rem;
  }

  .compact .odd-value {
    font-size: 1.375rem;
  }

  .odd-odds {
    font-size: 0.6875rem;
    font-weight: 600;
    opacity: 0.85;
  }

  .odd-bar {
    display: block;
    height: 4px;
    margin: 0 8px;
    border-radius: 999px;
    background: var(--track);
    overflow: hidden;
  }

  .overlay .odd-bar {
    background: rgba(255, 255, 255, 0.28);
  }

  .odd-bar > span {
    display: block;
    height: 100%;
    width: calc(var(--p) * 100%);
    border-radius: inherit;
    background: color-mix(in oklch, var(--prob-high) calc(var(--p) * 100%), var(--prob-low));
  }

  .overlay .odd-bar > span {
    background: var(--sky);
  }
</style>
