<!--
  Tile format `full`: like `banner`, but the photo or illustration fills
  the whole front of the collapsed card, down to its bottom edge: the title,
  the odds buttons and the "see all" bar are laid over it (the "live match"
  card of betting apps). The rest of the ranking opens below the image, on
  the card surface. Same options, same collapsed size
  and same back (KpiBack) as `banner`, and the same corner badges, stacked:
  time badge, then LIVE webcam link, Rewind or data from HH:MM.
-->
<script lang="ts">
  import BannerMedia from '../components/BannerMedia.svelte';
  import StaleBadge from '../components/StaleBadge.svelte';
  import WebcamBadge from '../components/WebcamBadge.svelte';
  import CertifiedBadge from '../components/CertifiedBadge.svelte';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { shortName } from '../lib/kpiView';
  import FlipCard from './FlipCard.svelte';
  import KpiBack from './KpiBack.svelte';
  import OddsRow from './OddsRow.svelte';
  import RankingMore from './RankingMore.svelte';
  import type { TileProps } from './registry';
  import TileBadge from './TileBadge.svelte';
  import TimeBadge from './TimeBadge.svelte';
  import { tileModel } from './tileModel';

  let { tile, view, webcam = null, time = null }: TileProps = $props();

  const model = $derived(tileModel(tile, view));
  const title = $derived(i18n.pick(tile.title ?? view.kpi.name));
  /** The period in words, for screen readers (the time badge is hidden from them). */
  const period = $derived(time ? i18n.pick(time.label) : '');
  /** Longer titles ("Poudreuse sur piste") get a smaller font, on up to two lines. */
  const LONG_TITLE = 24;

  let selected = $state<string | null>(null);
  let showAll = $state(false);

  const toggle = (stationId: string) => {
    selected = selected === stationId ? null : stationId;
  };
</script>

<FlipCard labelledby="{tile.id}-title" theme={model.theme}>
  {#snippet front()}
    <div class="hero">
      <BannerMedia
        scene={model.scene}
        skyline={model.skyline}
        photo={model.photo}
      />
      <div class="shade" aria-hidden="true"></div>
      {#if time || webcam || model.badge || model.staleSince}
        <span class="badge-slot">
          {#if time}<TimeBadge {time} onImage />{/if}
          {#if webcam}<WebcamBadge live={webcam} station={shortName(view, webcam.stationId)} />{/if}
          {#if model.badge}
            <TileBadge label={i18n.pick(model.badge)} icon="rewind" />
          {:else if model.staleSince}
            <StaleBadge since={model.staleSince} timezone={view.timezone} />
          {/if}
        </span>
      {/if}

      <div class="hero-content">
        <div class="title-row">
          <h2 id="{tile.id}-title" class:long={title.length > LONG_TITLE}>
            {title}{#if period}<span class="visually-hidden"> {period}</span>{/if}
          </h2>
          {#if view.kpi.certified}<CertifiedBadge size={22} onImage={true} />{/if}
        </div>
        {#if model.items.length === 0}
          <p class="sub">{i18n.t(model.emptyMessage)}</p>
        {:else}
          <OddsRow
            tileId={tile.id}
            label={period ? `${title} ${period}` : title}
            top={model.top}
            {selected}
            onselect={toggle}
          {view}
            showOdds={model.showOdds}
          details={model.details}
            overlay
          />
        {/if}
      </div>
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
    <KpiBack {tile} {view} {time} photo={model.photo} />
  {/snippet}
</FlipCard>

<style>
  .hero {
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    height: var(--tile-front-h);
    isolation: isolate;
  }

  /* The image and its shade run under the "see all" bar (.below), down to the
     bottom of the collapsed card; the card clips them. */
  .hero :global(.media) {
    z-index: -2;
    bottom: calc(-1 * var(--tile-more-h));
  }

  /* Darkens the lower half so white text and buttons stay legible on any image. */
  .shade {
    position: absolute;
    inset: 0 0 calc(-1 * var(--tile-more-h)) 0;
    z-index: -1;
    background: linear-gradient(
      180deg,
      rgba(3, 12, 30, 0.25) 0%,
      rgba(3, 12, 30, 0) 28%,
      rgba(3, 12, 30, 0.55) 58%,
      rgba(3, 12, 30, 0.88) 100%
    );
  }

  /* top 17px: the time badge (1.375rem) is centred on the "?" button. */
  .badge-slot {
    position: absolute;
    top: 17px;
    left: 12px;
    right: 56px; /* clear of the "?" button */
    display: flex;
    flex-direction: column; /* time badge first, LIVE / Rewind / stale under it */
    align-items: flex-start;
    gap: 6px;
  }

  .hero-content {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
    padding: 16px 14px 14px;
    color: #ffffff;
    text-align: center;
  }

  h2 {
    overflow: hidden;
    font-family: var(--font-display);
    letter-spacing: var(--display-tracking);
    font-size: 1.5rem;
    font-weight: var(--display-weight);
    line-height: 1.05;
    white-space: nowrap;
    text-overflow: ellipsis;
    text-shadow: 0 2px 12px rgba(0, 0, 0, 0.45);
  }

  h2.long {
    display: -webkit-box;
    font-size: 1.25rem;
    white-space: normal;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    line-clamp: 2;
  }

  .sub {
    margin-bottom: 8px;
    font-size: 0.8125rem;
    line-height: 1.35;
    color: rgba(255, 255, 255, 0.9);
  }

  .below {
    position: relative; /* above the image that runs under it */
    z-index: 1;
    display: grid;
    padding: 0 14px;
  }

  /* The first "see all" / "see less" button sits on the image. */
  .below > :global(.see-all:first-of-type) {
    color: #ffffff;
    border-top-color: rgba(255, 255, 255, 0.28);
    text-shadow: 0 1px 8px rgba(0, 0, 0, 0.35);
  }

  .below :global(.details) {
    margin: 12px 0;
  }

  /* Title and, for an official value, the "certified" rosette right after it. */
  .title-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    min-width: 0;
  }

  .title-row h2 {
    min-width: 0;
  }
</style>
