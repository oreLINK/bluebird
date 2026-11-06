<!--
  Static placeholder shown in place of a tile while its data loads. Mirrors
  the layout of the tile type (full, banner or compact). No
  animation, on purpose.
-->
<script lang="ts">
  import type { SkeletonVariant } from './registry';

  let {
    id,
    title,
    variant = 'compact',
  }: {
    id: string;
    title: string;
    variant?: SkeletonVariant;
  } = $props();
</script>

{#if variant === 'full'}
  <section class="card" aria-labelledby="{id}-title" aria-busy="true">
    <div class="card-body">
      <div class="full">
        <h2 id="{id}-title">{title}</h2>
        <div class="odds" aria-hidden="true">
          <span></span><span></span><span></span>
        </div>
      </div>
      <div class="more" aria-hidden="true"></div>
    </div>
  </section>
{:else if variant === 'banner'}
  <section class="card" aria-labelledby="{id}-title" aria-busy="true">
    <div class="card-body">
      <div class="banner"></div>
      <div class="content">
        <h2 id="{id}-title">{title}</h2>
        <div class="odds" aria-hidden="true">
          <span></span><span></span><span></span>
        </div>
      </div>
      <div class="more" aria-hidden="true"></div>
    </div>
  </section>
{:else}
  <section class="card" aria-labelledby="{id}-title" aria-busy="true">
    <div class="card-body">
      <div class="content compact">
        <span class="ticket" aria-hidden="true"></span>
        <h2 id="{id}-title">{title}</h2>
        <div class="odds" aria-hidden="true">
          <span></span><span></span><span></span>
        </div>
      </div>
      <div class="more" aria-hidden="true"></div>
    </div>
  </section>
{/if}

<style>
  .full {
    display: grid;
    align-content: end;
    gap: 14px;
    height: var(--tile-front-h);
    padding: 14px;
    text-align: center;
    background: var(--track);
  }

  .banner {
    height: var(--tile-banner-h);
    background: var(--track);
  }

  .content {
    display: grid;
    align-content: start;
    gap: 14px;
    height: calc(var(--tile-front-h) - var(--tile-banner-h));
    padding: 14px;
    text-align: center;
  }

  .content.compact {
    align-content: start;
    gap: 6px;
    height: var(--tile-compact-h);
    padding-top: 17px;
    text-align: left;
  }

  /* Place of the time badge (TimeBadge.svelte) of the compact tile. */
  .ticket {
    display: block;
    width: 6.5rem;
    height: 1.375rem;
    border-radius: 5px;
    background: var(--track);
  }

  .content.compact h2 {
    font-size: 1.375rem;
  }

  .content.compact .odds span {
    height: var(--odds-button-compact-h);
  }

  .more {
    height: var(--tile-more-h);
    border-top: 1px solid var(--line);
  }

  h2 {
    font-family: var(--font-display);
    letter-spacing: var(--display-tracking);
    font-size: 1.5rem;
    font-weight: var(--display-weight);
    color: var(--ink-faint);
  }

  .full .odds span {
    background: var(--surface);
  }

  .odds {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .odds span {
    display: block;
    height: var(--odds-button-h);
    border-radius: var(--radius-m);
    background: var(--track);
  }
</style>
