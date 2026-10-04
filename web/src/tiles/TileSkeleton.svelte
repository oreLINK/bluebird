<!--
  Static placeholder shown in place of a tile while its data loads. Mirrors
  the layout of the tile type (banner, full banner, simple or list). No
  animation, on purpose.
-->
<script lang="ts">
  import type { SkeletonVariant } from './registry';
  import TileShell from './TileShell.svelte';

  let {
    id,
    title,
    icon = null,
    variant = 'list',
  }: {
    id: string;
    title: string;
    icon?: string | null;
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
{:else if variant === 'simple'}
  <section class="card" aria-labelledby="{id}-title" aria-busy="true">
    <div class="card-body">
      <div class="content simple">
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
  <TileShell {id} {title} {icon} busy>
    <div class="rows" aria-hidden="true">
      {#each [0, 1, 2, 3, 4] as i (i)}
        <span></span>
      {/each}
    </div>
  </TileShell>
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

  .content.simple {
    align-content: center;
    gap: 6px;
    height: var(--tile-simple-h);
    padding-top: 8px;
    text-align: left;
  }

  .content.simple h2 {
    font-size: 1.375rem;
  }

  .content.simple .odds span {
    height: var(--odds-button-compact-h);
  }

  .more {
    height: var(--tile-more-h);
    border-top: 1px solid var(--line);
  }

  h2 {
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-style: italic;
    font-weight: 800;
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

  .odds span,
  .rows span {
    display: block;
    height: var(--odds-button-h);
    border-radius: var(--radius-m);
    background: var(--track);
  }

  .rows {
    display: grid;
    gap: 8px;
    padding-bottom: 10px;
  }

  .rows span {
    height: 3rem;
  }
</style>
