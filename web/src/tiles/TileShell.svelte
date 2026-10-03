<!--
  Shared container of every tile: frosted glass card with an icon, a title,
  an optional subtitle, the tile body and an optional footer.
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
    children,
    footer,
  }: {
    id: string;
    title: string;
    subtitle?: string;
    icon?: string | null;
    busy?: boolean;
    children: Snippet;
    footer?: Snippet;
  } = $props();
</script>

<section class="tile glass" aria-labelledby="{id}-title" aria-busy={busy}>
  <header class="head">
    {#if icon}
      <span class="icon"><Icon name={icon} size={22} /></span>
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
</section>

<style>
  .tile {
    display: flex;
    flex-direction: column;
    border-radius: var(--radius-l);
    padding: 16px 14px 14px;
    min-width: 0;
  }

  .head {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 0 4px 12px;
  }

  .icon {
    display: grid;
    place-items: center;
    flex: none;
    width: 40px;
    height: 40px;
    border-radius: 14px;
    color: var(--accent);
    background: var(--glass-bg-strong);
    border: 1px solid var(--glass-border);
  }

  h2 {
    font-size: 1.125rem;
    font-weight: 700;
    letter-spacing: -0.015em;
    line-height: 1.25;
  }

  .titles p {
    margin-top: 2px;
    font-size: 0.8125rem;
    color: var(--ink-faint);
    line-height: 1.35;
  }

  .body {
    flex: 1;
  }

  .foot {
    padding: 10px 4px 0;
  }
</style>
