<!--
  Decorative winter backdrop: two snowy ridgelines drawn from the massif's
  `skyline` points (config/massifs.yaml), plus stars that only show at night.
-->
<script lang="ts">
  let { skyline = [] }: { skyline?: number[] } = $props();

  const WIDTH = 1000;
  const HEIGHT = 320;

  /** Rugged ridge path through the points, closed along the bottom edge. */
  function ridge(points: number[], base: number, amplitude: number): string {
    const values = points.length >= 2 ? points : [0.4, 0.7, 0.5, 0.8, 0.45];
    const coords = values.map((v, i): [number, number] => [
      (i / (values.length - 1)) * WIDTH,
      HEIGHT - (base + v * amplitude),
    ]);
    let d = `M0 ${HEIGHT} L${coords[0]![0]} ${coords[0]![1]}`;
    for (let i = 1; i < coords.length; i++) {
      const [x0, y0] = coords[i - 1]!;
      const [x1, y1] = coords[i]!;
      // A shoulder a third of the way down the slope, so ridges look rocky.
      const sx = x0 + (x1 - x0) * (i % 2 ? 0.38 : 0.62);
      const sy = Math.max(y0, y1) - Math.abs(y1 - y0) * 0.35 + 10;
      d += ` L${sx.toFixed(1)} ${sy.toFixed(1)} L${x1.toFixed(1)} ${y1.toFixed(1)}`;
    }
    return `${d} L${WIDTH} ${HEIGHT} Z`;
  }

  const far = $derived(ridge(skyline, 120, 150));
  const near = $derived(ridge([...skyline].reverse().map((v) => 0.25 + v * 0.55), 30, 150));

  // Deterministic star field.
  const stars = Array.from({ length: 28 }, (_, i) => ({
    x: (i * 137.5) % 100,
    y: ((i * 61.8) % 38) + 2,
    r: i % 5 === 0 ? 0.22 : 0.13,
  }));
</script>

<div class="backdrop" aria-hidden="true">
  <svg class="stars" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice">
    {#each stars as star, i (i)}
      <circle cx={star.x} cy={star.y} r={star.r} />
    {/each}
  </svg>
  <svg class="ridges" viewBox="0 0 {WIDTH} {HEIGHT}" preserveAspectRatio="none">
    <defs>
      <linearGradient id="bb-near" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" style="stop-color: var(--ridge-near)" />
        <stop offset="100%" style="stop-color: var(--ridge-shade)" />
      </linearGradient>
    </defs>
    <path d={far} style="fill: var(--ridge-far)" />
    <path d={near} fill="url(#bb-near)" />
  </svg>
</div>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    overflow: hidden;
  }

  .stars {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    fill: var(--star);
  }

  .ridges {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: min(38vh, 340px);
  }
</style>
