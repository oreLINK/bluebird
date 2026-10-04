<!--
  Everything below the odds buttons of a tile (any KPI kind): the details of
  the selected top station (live only), the rest of the ranking when expanded, and the
  "see all" toggle. While expanded, a second "see less" button sits between
  the top stations and the list, so the list can be closed without scrolling
  down; focus then moves to the bottom toggle.
-->
<script lang="ts">
  import { tick } from 'svelte';
  import Icon from '../components/Icon.svelte';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import type { KpiView, RankItem } from '../lib/kpiView';
  import StationDetails from './StationDetails.svelte';
  import StationRow from './StationRow.svelte';

  let {
    tileId,
    view,
    top,
    rest,
    selected,
    onselect,
    showAll,
    ontoggleall,
    showOdds = false,
    showWindow = false,
    details = false,
  }: {
    tileId: string;
    view: KpiView;
    top: RankItem[];
    rest: RankItem[];
    selected: string | null;
    onselect: (stationId: string) => void;
    showAll: boolean;
    ontoggleall: () => void;
    showOdds?: boolean;
    showWindow?: boolean;
    /** Station rows open their details on tap (tile option `details`, live only). */
    details?: boolean;
  } = $props();

  const selectedTop = $derived(details ? top.find((i) => i.stationId === selected) : undefined);
  const total = $derived(top.length + rest.length);

  let bottomToggle = $state<HTMLButtonElement>();

  async function collapseFromTop() {
    ontoggleall();
    await tick();
    bottomToggle?.focus({ preventScroll: true });
  }
</script>

{#if selectedTop?.entry}
  <StationDetails
    id="{tileId}-top-details"
    entry={selectedTop.entry}
    kpi={view.kpi}
    station={view.stations[selectedTop.stationId]}
    timezone={view.timezone}
    {showWindow}
  />
{/if}

{#if rest.length > 0}
  {#if showAll}
    <button
      type="button"
      class="see-all"
      aria-expanded={showAll}
      aria-controls="{tileId}-rest"
      onclick={collapseFromTop}
    >
      {i18n.t('tile.seeLess')}
      <Icon name="chevron" size={16} class="flip" />
    </button>
    <ol class="rest" id="{tileId}-rest">
      {#each rest as item, index (item.stationId)}
        <StationRow
          id="{tileId}-{item.stationId}"
          rank={top.length + index + 1}
          {item}
          {view}
          open={selected === item.stationId}
          ontoggle={() => onselect(item.stationId)}
          {showOdds}
          {showWindow}
          {details}
        />
      {/each}
    </ol>
  {/if}
  <button
    bind:this={bottomToggle}
    type="button"
    class="see-all"
    aria-expanded={showAll}
    aria-controls={showAll ? `${tileId}-rest` : undefined}
    onclick={ontoggleall}
  >
    {showAll ? i18n.t('tile.seeLess') : i18n.t('tile.seeAll', { count: total })}
    <Icon name="chevron" size={16} class={showAll ? 'flip' : ''} />
  </button>
{:else}
  <div class="see-all-spacer" aria-hidden="true"></div>
{/if}

<style>
  .rest {
    margin: 0;
    padding: 0;
    border-top: 1px solid var(--line);
  }

  .see-all {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    width: calc(100% + 28px);
    margin: 0 -14px;
    height: var(--tile-more-h);
    border: 0;
    border-top: 1px solid var(--line);
    background: transparent;
    color: var(--link);
    font-size: 0.875rem;
    font-weight: 700;
    cursor: pointer;
  }

  .see-all-spacer {
    height: var(--tile-more-h);
  }

  .see-all :global(.flip) {
    transform: rotate(180deg);
  }
</style>
