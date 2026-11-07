<!--
  Compact value pill used in ranking rows: "82 %" (live) or "4,43 m"
  (historical), optionally with decimal odds below it. The magnitude is
  conveyed by the bar next to it, so the pill keeps one high-contrast colour
  pair (--pill-*, overridden by tile themes). A `scale` value ("4", avalanche
  danger) takes the colour of its level instead (`scale`: the step tone,
  tokens in styles/base.css).
-->
<script lang="ts">
  let { label, odds = '', scale }: { label: string; odds?: string; scale?: string } = $props();
</script>

<span class="pill tabular" data-scale={scale}>
  <span class="value">{label}</span>
  {#if odds}<span class="odds">{odds}</span>{/if}
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

  .pill[data-scale] {
    border-color: var(--scale-edge, color-mix(in srgb, var(--scale-bg) 70%, #000000));
    background: var(--scale-fill, var(--scale-bg));
    color: var(--scale-ink);
  }

  .pill[data-scale] .value {
    text-shadow: var(--scale-number-shadow, none);
  }

  .value {
    font-family: var(--font-display);
    letter-spacing: var(--display-tracking);
    font-size: 1.1875rem;
    font-weight: var(--display-weight);
    line-height: 1.05;
    white-space: nowrap;
  }

  .odds {
    font-size: 0.6875rem;
    font-weight: 600;
    opacity: 0.85;
  }
</style>
