<!--
  Card container for list-style tiles (TileRanking, TileSkeleton): the shared
  card frame, an icon chip, a title, an optional subtitle, the body and an
  optional footer. TileBanner builds its own layout on the same card frame.
-->
<script lang="ts">
  import type { Snippet } from 'svelte';
  import Icon from '../components/Icon.svelte';

  let {
    id,
    title,
    subtitle = '',
    icon = null,
    busy = false,
    framed = true,
    children,
    footer,
  }: {
    id: string;
    title: string;
    subtitle?: string;
    icon?: string | null;
    busy?: boolean;
    /** false: render only the content, for use inside FlipCard. */
    framed?: boolean;
    children: Snippet;
    footer?: Snippet;
  } = $props();
</script>

{#snippet content()}
  <header class="head">
    {#if icon}
      <span class="icon"><Icon name={icon} size={20} /></span>
    {/if}
    <div class="titles">
      <h2 id="{id}-title">{title}</h2>
      {#if subtitle}<p>{subtitle}</p>{/if}
    </div>
  </header>
  <div class="body">
    {@render children()}
  </div>
  {#if footer}
    <footer class="foot">{@render footer()}</footer>
  {/if}
{/snippet}

{#if framed}
  <section class="card" aria-labelledby="{id}-title" aria-busy={busy}>
    <div class="card-body">{@render content()}</div>
  </section>
{:else}
  {@render content()}
{/if}

<style>
  .head {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 14px 56px 10px 14px;
  }

  .icon {
    display: grid;
    place-items: center;
    flex: none;
    width: 38px;
    height: 38px;
    border-radius: 12px;
    color: var(--pill-ink);
    background: var(--pill-bg);
  }

  h2 {
    font-family: var(--font-display);
    font-size: 1.375rem;
    font-style: italic;
    font-weight: 800;
    line-height: 1.15;
  }

  .titles p {
    margin-top: 2px;
    font-size: 0.8125rem;
    color: var(--ink-faint);
    line-height: 1.35;
  }

  .body {
    padding: 0 14px 6px;
  }
</style>
