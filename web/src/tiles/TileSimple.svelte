<!--
  Tile type `simple`: a `banner` tile without the banner, for the KPIs lower
  on the page. Same width and same parts on a FlipCard, but shorter:
    Front: title (no icon), the best stations as odds buttons (OddsRow), then
           "see all" for the rest (RankingMore).
    Back:  KpiBack, like every tile.
  Every simple tile has the same collapsed size (--tile-simple-h in base.css).
  Options (config/tiles.yaml):
    top:       number of odds buttons, 1–3 (default 3)
    show_odds: also show decimal odds 1/p (default false)
    details:   tapping a station shows its details (default false for now)
-->
<script lang="ts">
  import { i18n } from '../lib/i18n/i18n.svelte';
  import FlipCard from './FlipCard.svelte';
  import KpiBack from './KpiBack.svelte';
  import OddsRow from './OddsRow.svelte';
  import RankingMore from './RankingMore.svelte';
  import type { TileProps } from './registry';
  import StaleBadge from '../components/StaleBadge.svelte';
  import TileBadge from './TileBadge.svelte';
  import { tileModel } from './tileModel';

  let { tile, view }: TileProps = $props();

  const model = $derived(tileModel(tile, view));
  const title = $derived(i18n.pick(tile.title ?? view.kpi.name));
  /** Longer titles ("… demain après-midi") get a smaller font, on up to two lines. */
  const LONG_TITLE = 24;

  let selected = $state<string | null>(null);
  let showAll = $state(false);

  const toggle = (stationId: string) => {
    selected = selected === stationId ? null : stationId;
  };
</script>

<FlipCard labelledby="{tile.id}-title" plain theme={model.theme}>
  {#snippet front()}
    <div class="content">
      <header class="headline">
        {#if model.badge}
          <TileBadge label={i18n.pick(model.badge)} icon="rewind" />
        {:else if model.staleSince}
          <StaleBadge since={model.staleSince} timezone={view.timezone} />
        {/if}
        <h2 id="{tile.id}-title" class:long={title.length > LONG_TITLE}>{title}</h2>
      </header>
      {#if model.items.length === 0}
        <p class="empty">{i18n.t(model.emptyMessage)}</p>
      {:else}
        <OddsRow
          tileId={tile.id}
          label={title}
          top={model.top}
          {selected}
          onselect={toggle}
          {view}
          showOdds={model.showOdds}
          details={model.details}
        />
      {/if}
    </div>

    <div class="below">
      <RankingMore
        tileId={tile.id}
        {view}
        top={model.top}
        rest={model.rest}
        {selected}
        onselect={toggle}
        {showAll}
        ontoggleall={() => (showAll = !showAll)}
        showOdds={model.showOdds}
        details={model.details}
        showWindow={!model.timeWindow}
      />
    </div>
  {/snippet}

  {#snippet back()}
    <KpiBack {tile} {view} photo={model.photo} />
  {/snippet}
</FlipCard>

<style>
  .content {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    align-content: center;
    gap: 12px;
    height: var(--tile-simple-h);
    padding: 12px 14px 0;
    overflow: hidden;
  }

  .headline {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    /* Room for the "?" button of the FlipCard. */
    padding-right: 40px;
  }

  h2 {
    overflow: hidden;
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-style: italic;
    font-weight: 800;
    line-height: 1.1;
    min-width: 0;
    white-space: nowrap;
    text-overflow: ellipsis;
    color: var(--tile-title, inherit);
  }

  h2.long {
    display: -webkit-box;
    font-size: 1.25rem;
    white-space: normal;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    line-clamp: 2;
  }

  .empty {
    text-align: center;
    font-size: 0.875rem;
    color: var(--ink-faint);
  }

  .below {
    display: grid;
    padding: 0 14px;
  }

  .below :global(.details) {
    margin-bottom: 12px;
  }
</style>
