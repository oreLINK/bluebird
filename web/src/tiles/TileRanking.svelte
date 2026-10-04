<!--
  Tile type `ranking`: a compact list of every station sorted by probability.
  Reads the first KPI of the tile. Options (config/tiles.yaml):
    visible_rows: rows shown before "see all" (default 5)
    show_odds:    also show decimal odds 1/p (default false)
  Tapping a row reveals the explanatory drivers declared in config/kpis.yaml.
  The "?" button (or a tap outside the rows) flips it to KpiBack.
-->
<script lang="ts">
  import StaleBadge from '../components/StaleBadge.svelte';
  import { formatWindow } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { sharedWindow } from '../lib/ranking';
  import { booleanOption, numberOption } from './options';
  import type { TileProps } from './registry';
  import FlipCard from './FlipCard.svelte';
  import KpiBack from './KpiBack.svelte';
  import StationRow from './StationRow.svelte';
  import TileShell from './TileShell.svelte';

  let { tile, kpis, data }: TileProps = $props();

  const kpi = $derived(kpis[0]);
  const view = $derived(kpi ? data.kpis[kpi.id] : undefined);
  const ranking = $derived(view?.ranking ?? []);
  const visibleRows = $derived(numberOption(tile.options, 'visible_rows', 5));
  const showOdds = $derived(booleanOption(tile.options, 'show_odds', false));

  let showAll = $state(false);
  let openStation = $state<string | null>(null);

  const rows = $derived(showAll ? ranking : ranking.slice(0, visibleRows));
  const title = $derived(i18n.pick(tile.title ?? kpi?.name));
  const timeWindow = $derived(sharedWindow(ranking));

  function toggle(stationId: string) {
    openStation = openStation === stationId ? null : stationId;
  }
</script>

<FlipCard labelledby="{tile.id}-title">
  {#snippet front()}
    <TileShell id={tile.id} {title} icon={tile.icon} framed={false}>
      {#if view?.stale}
        <StaleBadge since={view.generated_at} timezone={data.timezone} />
      {/if}
      {#if ranking.length === 0}
        <p class="note">{i18n.t('tile.noRanking')}</p>
      {:else}
        {#if timeWindow}
          <p class="note tabular">
            {i18n.t('tile.window')} · {formatWindow(
              timeWindow.start,
              timeWindow.end,
              i18n.locale,
              data.timezone,
            )}
          </p>
        {/if}
        <ol class="ranking">
          {#each rows as entry, index (entry.station_id)}
            <StationRow
              id="{tile.id}-{entry.station_id}"
              rank={index + 1}
              {entry}
              {kpi}
              station={data.stations[entry.station_id]}
              timezone={data.timezone}
              open={openStation === entry.station_id}
              ontoggle={() => toggle(entry.station_id)}
              {showOdds}
              showWindow={!timeWindow}
            />
          {/each}
        </ol>
      {/if}

      {#snippet footer()}
        {#if ranking.length > visibleRows}
          <button type="button" class="more" aria-expanded={showAll} onclick={() => (showAll = !showAll)}>
            {showAll ? i18n.t('tile.seeLess') : i18n.t('tile.seeAll', { count: ranking.length })}
          </button>
        {/if}
      {/snippet}
    </TileShell>
  {/snippet}
  {#snippet back()}
    <KpiBack {tile} {kpi} {data} />
  {/snippet}
</FlipCard>

<style>
  .note {
    padding: 0 0 6px;
    font-size: 0.8125rem;
    color: var(--ink-faint);
  }

  .ranking {
    margin: 0;
    padding: 0;
  }

  .more {
    width: 100%;
    height: var(--tile-more-h);
    border: 0;
    border-top: 1px solid var(--line);
    background: transparent;
    color: var(--link);
    font-size: 0.875rem;
    font-weight: 700;
    cursor: pointer;
  }
</style>
