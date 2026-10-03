<!-- Horizontally scrollable chips, one per enabled massif (config/massifs.yaml). -->
<script lang="ts">
  import type { Massif } from '../lib/config';
  import { i18n } from '../lib/i18n/i18n.svelte';

  let {
    massifs,
    selected,
    onselect,
  }: { massifs: Massif[]; selected: string; onselect: (id: string) => void } = $props();
</script>

<nav class="picker" aria-label={i18n.t('header.massif')}>
  {#each massifs as massif (massif.id)}
    <button
      type="button"
      class="chip"
      aria-pressed={massif.id === selected}
      onclick={() => onselect(massif.id)}
    >
      {i18n.pick(massif.name)}
    </button>
  {/each}
</nav>

<style>
  .picker {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    scrollbar-width: none;
    scroll-snap-type: x proximity;
    padding: 2px 0;
  }

  .picker::-webkit-scrollbar {
    display: none;
  }

  .chip {
    flex: none;
    scroll-snap-align: start;
    min-height: 2.25rem;
    padding: 0 1rem;
    border-radius: 999px;
    border: 1px solid var(--glass-border);
    background: var(--glass-bg);
    color: var(--ink-soft);
    font-size: 0.9375rem;
    font-weight: 600;
    cursor: pointer;
    transition:
      background 0.2s ease,
      color 0.2s ease;
  }

  .chip[aria-pressed='true'] {
    background: var(--accent);
    border-color: transparent;
    color: var(--accent-ink);
    box-shadow: 0 6px 16px -8px var(--accent);
  }
</style>
