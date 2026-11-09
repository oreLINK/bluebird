<!--
  "Certified" rosette in the corner badges of a tile (after the time badge), whose value comes as is from
  an official source (KPI `certified` in config/kpis.yaml, e.g. the
  Météo-France avalanche bulletin), like the verified badge of social
  networks. A blue scalloped rosette with a white check mark (--verified-*
  tokens); the tile back explains it. Not interactive: a tap flips the card,
  which shows that explanation.
-->
<script lang="ts">
  import { i18n } from '../lib/i18n/i18n.svelte';

  let { size = 20, onImage = false }: { size?: number; onImage?: boolean } = $props();

  // Ten scallops around the centre (radius 10.5 ± 1.2), drawn once.
  const ROSETTE = (() => {
    const points: string[] = [];
    for (let i = 0; i < 120; i++) {
      const angle = (i / 120) * 2 * Math.PI;
      const radius = 9.3 + 1.2 * Math.cos(10 * angle);
      points.push(`${(12 + radius * Math.sin(angle)).toFixed(1)} ${(12 - radius * Math.cos(angle)).toFixed(1)}`);
    }
    return `M${points.join('L')}Z`;
  })();
</script>

<svg
  class="certified"
  class:on-image={onImage}
  viewBox="0 0 24 24"
  width={size}
  height={size}
  role="img"
  aria-label={i18n.t('tile.certified')}
>
  <path d={ROSETTE} style="fill: var(--verified-bg)" />
  <path
    d="M7.7 12.3 L10.6 15.1 L16.3 9.3"
    style="fill: none; stroke: var(--verified-ink); stroke-width: 2.3; stroke-linecap: round; stroke-linejoin: round"
  />
</svg>

<style>
  .certified {
    flex: none;
    display: block;
  }

  .on-image {
    filter: drop-shadow(0 1px 4px rgba(0, 0, 0, 0.45));
  }
</style>
