<!--
  Compact "odds button" used in ranking rows: the probability as a
  percentage on a light-blue pill, optionally with decimal odds (1/p). The
  magnitude is conveyed by the probability bar next to it, so the pill keeps
  one high-contrast colour pair.
-->
<script lang="ts">
  import { formatOdds, formatPercent } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';

  let { probability, showOdds = false }: { probability: number; showOdds?: boolean } = $props();
</script>

<span class="pill tabular">
  <span class="pct">{formatPercent(probability, i18n.locale)}</span>
  {#if showOdds}
    <span class="odds">{i18n.t('tile.odds', { odds: formatOdds(probability, i18n.locale) })}</span>
  {/if}
</span>

<style>
  .pill {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-width: 4.25rem;
    padding: 0.4rem 0.6rem;
    border-radius: var(--radius-s);
    border: 1px solid var(--pill-border);
    background: var(--pill-bg);
    color: var(--pill-ink);
  }

  .pct {
    font-family: var(--font-display);
    font-size: 1.1875rem;
    font-style: italic;
    font-weight: 800;
    line-height: 1.05;
  }

  .odds {
    font-size: 0.6875rem;
    font-weight: 600;
    opacity: 0.85;
  }
</style>
