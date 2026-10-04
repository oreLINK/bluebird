<!--
  Small label in a corner of a tile, e.g. "REWIND 25/26" on the tiles of a
  historical KPI. Colours: --tile-badge-bg / --tile-badge-ink (tile theme).
-->
<script lang="ts">
  import Icon from '../components/Icon.svelte';

  let { label, icon = '' }: { label: string; icon?: string } = $props();
</script>

<span class="badge">
  {#if icon}<Icon name={icon} size={14} />{/if}
  {label}
</span>

<style>
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    height: 1.625rem;
    padding: 0 10px 0 8px;
    border-radius: 999px;
    background: var(--tile-badge-bg, var(--brand));
    color: var(--tile-badge-ink, var(--on-brand));
    font-size: 0.6875rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    white-space: nowrap;
  }
</style>
