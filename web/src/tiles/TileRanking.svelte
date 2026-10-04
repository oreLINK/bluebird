<!--
  Tile type `ranking`: a compact list of every station sorted by probability.
  Reads the first KPI of the tile, live or historical (lib/kpiView.ts). Options (config/tiles.yaml):
    visible_rows: rows shown before "see all" (default 5)
    show_odds:    also show decimal odds 1/p (default false)
    details:      tapping a row reveals the explanatory drivers declared in
                  config/kpis.yaml (default false for now)
  The "?" button (or a tap outside the rows) flips it to KpiBack.
-->
<script lang="ts">
  import StaleBadge from '../components/StaleBadge.svelte';
  import { formatWindow } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { numberOption } from './options';
  import type { TileProps } from './registry';
  import { tileModel } from './tileModel';
  import FlipCard from './FlipCard.svelte';
  import KpiBack from './KpiBack.svelte';
  import StationRow from './StationRow.svelte';
  import TileShell from './TileShell.svelte';

  let { tile, view }: TileProps = $props();

  const model = $derived(tileModel(tile, view));
  const ranking = $derived(model.items);
  const visibleRows = $derived(numberOption(tile.options, 'visible_rows', 5));

  let showAll = $state(false);
  let openStation = $state<string | null>(null);

  const rows = $derived(showAll ? ranking : ranking.slice(0, visibleRows));
  const title = $derived(i18n.pick(tile.title ?? view.kpi.name));
  const timeWindow = $derived(model.timeWindow);

  function toggle(stationId: string) {
    openStation = openStation === stationId ? null : stationId;
  }
</script>

<FlipCard labelledby="{tile.id}-title" theme={model.theme}>
  {#snippet front()}
    <TileShell id={tile.id} {title} icon={tile.icon} framed={false}>
      {#if model.staleSince}
        <StaleBadge since={model.staleSince} timezone={view.timezone} />
      {/if}
      {#if ranking.length === 0}
        <p class="note">{i18n.t(model.emptyMessage)}</p>
      {:else}
        {#if timeWindow}
          <p class="note tabular">
            {i18n.t('tile.window')} · {formatWindow(
              timeWindow.start,
              timeWindow.end,
              i18n.locale,
              view.timezone,
            )}
          </p>
        {/if}
        <ol class="ranking">
          {#each rows as item, index (item.stationId)}
            <StationRow
              id="{tile.id}-{item.stationId}"
              rank={index + 1}
              {item}
              {view}
              open={openStation === item.stationId}
              ontoggle={() => toggle(item.stationId)}
              showOdds={model.showOdds}
              showWindow={!timeWindow}
              details={model.details}
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
    <KpiBack {tile} {view} />
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
