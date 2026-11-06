<!--
  Tile format `compact`: a `banner` tile without the image, for the KPIs lower
  on the page. Same width and same parts on a FlipCard, but shorter:
    Front: a row of badges level with the "?" button (time badge, or the
           Rewind / "data from HH:MM" badge), the title (no icon, no period),
           the best stations as odds buttons (OddsRow), then "see all" for
           the rest (RankingMore).
    Back:  KpiBack, like every tile.
  Every compact tile has the same collapsed size (--tile-compact-h in base.css).
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
  import TimeBadge from './TimeBadge.svelte';
  import { tileModel } from './tileModel';

  let { tile, view, time = null }: TileProps = $props();

  const model = $derived(tileModel(tile, view));
  const title = $derived(i18n.pick(tile.title ?? view.kpi.name));
  /** The period in words, for screen readers (the time badge is hidden from them). */
  const period = $derived(time ? i18n.pick(time.label) : '');
  /** Longer titles ("Nieve polvo fuera de pista") get a smaller font, still on one line. */
  const LONG_TITLE = 20;

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
        {#if time || model.badge || model.staleSince}
          <div class="badges">
            {#if time}<TimeBadge {time} />{/if}
            {#if model.badge}
              <TileBadge label={i18n.pick(model.badge)} icon="rewind" />
            {:else if model.staleSince}
              <StaleBadge since={model.staleSince} timezone={view.timezone} />
            {/if}
          </div>
        {/if}
        <h2 id="{tile.id}-title" class:long={title.length > LONG_TITLE}>
          {title}{#if period}<span class="visually-hidden"> {period}</span>{/if}
        </h2>
      </header>
      {#if model.items.length === 0}
        <p class="empty">{i18n.t(model.emptyMessage)}</p>
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
          compact
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
    <KpiBack {tile} {view} {time} photo={model.photo} />
  {/snippet}
</FlipCard>

<style>
  /* The badge row (1.375rem) is centred on the "?" button of the FlipCard
     (top 10px, 2.25rem): 17px from the top. */
  .content {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    align-content: start;
    gap: 6px;
    height: var(--tile-compact-h);
    padding: 17px 14px 0;
    overflow: hidden;
  }

  .headline {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 6px;
    min-width: 0;
  }

  .badges {
    display: flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
    height: 1.375rem;
    /* Room for the "?" button of the FlipCard. */
    padding-right: 44px;
  }

  h2 {
    overflow: hidden;
    font-family: var(--font-display);
    letter-spacing: var(--display-tracking);
    font-size: 1.375rem;
    font-weight: var(--display-weight);
    line-height: 1.1;
    min-width: 0;
    white-space: nowrap;
    text-overflow: ellipsis;
    color: var(--tile-title, inherit);
  }

  h2.long {
    font-size: 1.125rem;
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
