<!--
  Betting-style "odds button": the probability as a percentage, coloured on a
  slate -> glacier-blue scale, optionally with decimal odds (1/p).
-->
<script lang="ts">
  import { formatOdds, formatPercent } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';

  let { probability, showOdds = false }: { probability: number; showOdds?: boolean } = $props();
</script>

<span class="pill tabular" style="--p: {probability}">
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
    color: var(--prob-ink);
    background: color-mix(in oklch, var(--prob-high) calc(var(--p) * 100%), var(--prob-low));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.28),
      0 4px 12px -6px color-mix(in oklch, var(--prob-high) 80%, transparent);
  }

  .pct {
    font-size: 1.0625rem;
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -0.01em;
  }

  .odds {
    font-size: 0.6875rem;
    font-weight: 600;
    opacity: 0.88;
  }
</style>
