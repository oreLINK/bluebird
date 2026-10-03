<!--
  Tile type `banner_full`: like `banner`, but the photo or illustration fills
  the whole front of the card, with the title and the odds buttons laid over
  it (the "live match" card of betting apps). Details and the rest of the
  ranking open below, on the card surface. Same options, same collapsed size
  and same back (KpiBack) as `banner`.
-->
<script lang="ts">
  import BannerMedia from '../components/BannerMedia.svelte';
  import PhotoCredit from '../components/PhotoCredit.svelte';
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

  let selected = $state<string | null>(null);
  let showAll = $state(false);

  const toggle = (stationId: string) => {
    selected = selected === stationId ? null : stationId;
  };
</script>

<FlipCard labelledby="{tile.id}-title">
  {#snippet front()}
    <div class="hero">
      <BannerMedia
        scene={model.scene}
        skyline={model.skyline}
        photo={model.photo}
        showCredit={false}
      />
      <div class="shade" aria-hidden="true"></div>

      <div class="hero-content">
        <h2 id="{tile.id}-title">{title}</h2>
        {#if model.ranking.length === 0}
          <p class="sub">{i18n.t('tile.noRanking')}</p>
        {:else}
          <OddsRow
            tileId={tile.id}
            label={title}
            top={model.top}
            {selected}
            onselect={toggle}
            stations={data.stations}
            showOdds={model.showOdds}
            overlay
          />
        {/if}
        {#if model.photo?.credit}
          <p class="credit"><PhotoCredit credit={model.photo.credit} /></p>
        {/if}
      </div>
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
  .hero {
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    height: var(--tile-front-h);
    overflow: hidden;
    isolation: isolate;
  }

  .hero :global(.media) {
    z-index: -2;
  }

  /* Darkens the lower half so white text and buttons stay legible on any image. */
  .shade {
    position: absolute;
    inset: 0;
    z-index: -1;
    background: linear-gradient(
      180deg,
      rgba(3, 12, 30, 0.25) 0%,
      rgba(3, 12, 30, 0) 28%,
      rgba(3, 12, 30, 0.55) 58%,
      rgba(3, 12, 30, 0.88) 100%
    );
  }

  .hero-content {
    display: grid;
    gap: 12px;
    padding: 16px 14px 14px;
    color: #ffffff;
    text-align: center;
  }

  h2 {
    overflow: hidden;
    font-family: var(--font-display);
    font-size: 1.875rem;
    font-style: italic;
    font-weight: 800;
    line-height: 1.05;
    white-space: nowrap;
    text-overflow: ellipsis;
    text-shadow: 0 2px 12px rgba(0, 0, 0, 0.45);
  }

  .sub {
    margin-bottom: 8px;
    font-size: 0.8125rem;
    line-height: 1.35;
    color: rgba(255, 255, 255, 0.9);
  }

  .credit {
    display: flex;
    justify-content: flex-end;
    margin-top: 2px;
  }

  .below {
    display: grid;
    padding: 0 14px;
  }

  .below :global(.details) {
    margin: 12px 0;
  }
</style>
