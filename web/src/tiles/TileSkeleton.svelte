<!-- Placeholder shown in place of a tile while its data loads. -->
<script lang="ts">
  import TileShell from './TileShell.svelte';

  let { id, title, icon = null }: { id: string; title: string; icon?: string | null } = $props();
</script>

<TileShell {id} {title} {icon} busy>
  <div class="rows" aria-hidden="true">
    {#each [0, 1, 2, 3, 4] as i (i)}
      <span class="row" style="animation-delay: {i * 80}ms"></span>
    {/each}
  </div>
</TileShell>

<style>
  .rows {
    display: grid;
    gap: 6px;
  }

  .row {
    height: 3.5rem;
    border-radius: var(--radius-m);
    background: linear-gradient(
      90deg,
      var(--track) 0%,
      var(--glass-bg-strong) 50%,
      var(--track) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.4s ease-in-out infinite;
  }

  @keyframes shimmer {
    from {
      background-position: 100% 0;
    }
    to {
      background-position: -100% 0;
    }
  }
</style>
