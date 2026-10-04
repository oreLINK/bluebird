<!--
  Tile type `banner`: a betting-app style card for one KPI, on a FlipCard.
  Front:
    1. Banner: the tile photo or an illustration, with the "?" button.
    2. Title (the description is on the back).
    3. The best stations as "odds buttons" (short name + percentage) with a
       probability bar below each. Tapping one shows its details.
    4. "See all" expands the rest of the ranking.
  Back: KpiBack (what the KPI is, how it is computed, today's reliability).
  Every banner tile has the same collapsed size (--tile-* in base.css).
  Options (config/tiles.yaml):
    top:       number of odds buttons, 1–3 (default 3)
    show_odds: also show decimal odds 1/p (default false)
    scene:     illustration (snowfall, piste, offpiste, mountain); default from icon
    photo:     none (default) | leader (ski area ranked first) | <path> (lib/photos.ts)
-->
<script lang="ts">
  import BannerMedia from '../components/BannerMedia.svelte';
  import StaleBadge from '../components/StaleBadge.svelte';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { bannerModel } from './bannerModel';
  import FlipCard from './FlipCard.svelte';
  import KpiBack from './KpiBack.svelte';
  import OddsRow from './OddsRow.svelte';
  import RankingMore from './RankingMore.svelte';
  import type { TileProps } from './registry';

  let { tile, kpis, data }: TileProps = $props();

  const model = $derived(bannerModel(tile, kpis, data));
  const title = $derived(i18n.pick(tile.title ?? model.kpi?.name));
  /** Longer titles ("… demain après-midi") get a smaller font, on up to two lines. */
  const LONG_TITLE = 24;

  let selected = $state<string | null>(null);
  let showAll = $state(false);

  const toggle = (stationId: string) => {
    selected = selected === stationId ? null : stationId;
  };
</script>

<FlipCard labelledby="{tile.id}-title">
  {#snippet front()}
    <header class="banner">
      <BannerMedia scene={model.scene} skyline={model.skyline} photo={model.photo} />
      {#if model.staleSince}
        <StaleBadge class="corner-badge" since={model.staleSince} timezone={data.timezone} />
      {/if}
    </header>

    <div class="content">
      <div class="headline">
        <h2 id="{tile.id}-title" class:long={title.length > LONG_TITLE}>{title}</h2>
      </div>
      {#if model.ranking.length === 0}
        <p class="empty">{i18n.t('tile.noRanking')}</p>
      {:else}
        <OddsRow
          tileId={tile.id}
          label={title}
          top={model.top}
          {selected}
          onselect={toggle}
          stations={data.stations}
          showOdds={model.showOdds}
        />
      {/if}
    </div>

    <div class="below">
      <RankingMore
        tileId={tile.id}
        kpi={model.kpi}
        {data}
        top={model.top}
        rest={model.rest}
        total={model.ranking.length}
        {selected}
        onselect={toggle}
        {showAll}
        ontoggleall={() => (showAll = !showAll)}
        showOdds={model.showOdds}
        showWindow={!model.timeWindow}
      />
    </div>
  {/snippet}

  {#snippet back()}
    <KpiBack {tile} kpi={model.kpi} {data} />
  {/snippet}
</FlipCard>

<style>
  .banner {
    position: relative;
    height: var(--tile-banner-h);
    overflow: hidden;
  }

  .banner :global(.corner-badge) {
    position: absolute;
    top: 10px;
    left: 10px;
  }

  .content {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    align-content: center;
    gap: 12px;
    height: calc(var(--tile-front-h) - var(--tile-banner-h));
    padding: 14px 14px 0;
    overflow: hidden;
  }

  .headline {
    text-align: center;
  }

  h2 {
    overflow: hidden;
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-style: italic;
    font-weight: 800;
    line-height: 1.1;
    white-space: nowrap;
    text-overflow: ellipsis;
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
