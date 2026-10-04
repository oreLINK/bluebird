<!--
  Everything below the odds buttons of a banner tile: the details of the
  selected top station, the rest of the ranking when expanded, and the
  "see all" toggle.
-->
<script lang="ts">
  import Icon from '../components/Icon.svelte';
  import type { Kpi } from '../lib/config';
  import type { RankingEntry } from '../lib/data';
  import type { MassifView } from '../lib/periods';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import StationDetails from './StationDetails.svelte';
  import StationRow from './StationRow.svelte';

  let {
    tileId,
    kpi,
    data,
    top,
    rest,
    total,
    selected,
    onselect,
    showAll,
    ontoggleall,
    showOdds = false,
    showWindow = false,
  }: {
    tileId: string;
    kpi: Kpi | undefined;
    data: MassifView;
    top: RankingEntry[];
    rest: RankingEntry[];
    total: number;
    selected: string | null;
    onselect: (stationId: string) => void;
    showAll: boolean;
    ontoggleall: () => void;
    showOdds?: boolean;
    showWindow?: boolean;
  } = $props();

  const selectedTop = $derived(top.find((e) => e.station_id === selected));
</script>

{#if selectedTop}
  <StationDetails
    id="{tileId}-top-details"
    entry={selectedTop}
    {kpi}
    station={data.stations[selectedTop.station_id]}
    timezone={data.timezone}
    {showWindow}
  />
{/if}

{#if rest.length > 0}
  {#if showAll}
    <ol class="rest">
      {#each rest as entry, index (entry.station_id)}
        <StationRow
          id="{tileId}-{entry.station_id}"
          rank={top.length + index + 1}
          {entry}
          {kpi}
          station={data.stations[entry.station_id]}
          timezone={data.timezone}
          open={selected === entry.station_id}
          ontoggle={() => onselect(entry.station_id)}
          {showOdds}
          {showWindow}
        />
      {/each}
    </ol>
  {/if}
  <button type="button" class="see-all" aria-expanded={showAll} onclick={ontoggleall}>
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
