<!--
  One ranked station: rank, name (with reliability dots for live KPIs), bar
  and value pill. Shared by every tile type and both KPI kinds (lib/kpiView.ts).
  With `details` (live only), the row is a button that toggles its
  StationDetails; without (the default for now), it is a static row and a tap
  on it does nothing (not even a flip).
-->
<script lang="ts">
  import ConfidenceDots from '../components/ConfidenceDots.svelte';
  import Icon from '../components/Icon.svelte';
  import ValuePill from '../components/ValuePill.svelte';
  import { formatOdds } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { type KpiView, type RankItem, fullName, itemLabel, itemNote, shortName } from '../lib/kpiView';
  import StationDetails from './StationDetails.svelte';
  import { itemSummary } from './summary';

  let {
    id,
    rank,
    item,
    view,
    open,
    ontoggle,
    showOdds = false,
    showWindow = false,
    details = false,
  }: {
    id: string;
    rank: number;
    item: RankItem;
    view: KpiView;
    open: boolean;
    ontoggle: () => void;
    showOdds?: boolean;
    showWindow?: boolean;
    details?: boolean;
  } = $props();

  const summary = $derived(itemSummary(view, item, rank, fullName(view, item.stationId), i18n));
  const interactive = $derived(details && !!item.entry);
</script>

{#snippet cells()}
  <span class="rank tabular" aria-hidden="true">{rank}</span>
  <span class="who" aria-hidden="true">
    <span class="name-line">
      <span class="name">{shortName(view, item.stationId)}</span>
      {#if item.confidence}<ConfidenceDots level={item.confidence} size={5} />{/if}
    </span>
    <span class="bar"><span style="--p: {item.share}"></span></span>
  </span>
  <span aria-hidden="true">
    <ValuePill
      label={itemLabel(view, item, i18n.locale)}
      odds={itemNote(item, i18n.locale) ||
        (showOdds ? i18n.t('tile.odds', { odds: formatOdds(item.value, i18n.locale) }) : '')}
    />
  </span>
{/snippet}

<li class:open>
  {#if interactive}
    <button
      type="button"
      class="row"
      aria-expanded={open}
      aria-controls="{id}-details"
      aria-label={summary}
      onclick={ontoggle}
    >
      {@render cells()}
      <Icon name="chevron" size={18} class="chevron" />
    </button>
  {:else}
    <div class="row static" data-no-flip>
      <span class="visually-hidden">{summary}</span>
      {@render cells()}
    </div>
  {/if}
  {#if interactive && open && item.entry}
    <div class="details-wrap">
      <StationDetails
        id="{id}-details"
        entry={item.entry}
        kpi={view.kpi}
        station={view.stations[item.stationId]}
        timezone={view.timezone}
        {showWindow}
      />
    </div>
  {/if}
</li>

<style>
  li {
    list-style: none;
    border-bottom: 1px solid var(--line);
  }

  li:last-child {
    border-bottom: 0;
  }

  .row {
    display: grid;
    grid-template-columns: 1.5rem minmax(0, 1fr) auto 18px;
    align-items: center;
    gap: 10px;
    width: 100%;
    min-height: 3.5rem;
    padding: 8px 4px;
    border: 0;
    background: transparent;
    text-align: left;
    cursor: pointer;
  }

  .row.static {
    grid-template-columns: 1.5rem minmax(0, 1fr) auto;
    cursor: default;
  }

  .rank {
    font-size: 0.9375rem;
    font-weight: 700;
    color: var(--ink-faint);
    text-align: center;
  }

  .who {
    display: grid;
    gap: 6px;
    min-width: 0;
  }

  .name-line {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }

  .name-line :global(.dots) {
    flex: none;
  }

  .name {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    overflow: hidden;
    font-weight: 600;
    font-size: 0.9375rem;
    line-height: 1.25;
    overflow-wrap: anywhere;
  }

  .bar {
    display: block;
    height: 4px;
    border-radius: 999px;
    background: var(--track);
    overflow: hidden;
  }

  .bar > span {
    display: block;
    height: 100%;
    width: calc(var(--p) * 100%);
    border-radius: inherit;
    background: color-mix(in oklch, var(--prob-high) calc(var(--p) * 100%), var(--prob-low));
  }

  .row :global(.chevron) {
    color: var(--ink-faint);
    transition: transform 0.2s ease;
  }

  li.open .row :global(.chevron) {
    transform: rotate(180deg);
  }

  .details-wrap {
    padding: 0 0 12px 34px;
  }
</style>
