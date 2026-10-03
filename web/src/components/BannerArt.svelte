<!--
  Static illustration at the top of a `banner` tile: a sky, two ridgelines
  drawn from the massif `skyline` (config/massifs.yaml) and a motif per scene:
    snowfall  falling snowflakes
    piste     a groomed piste with marker poles
    offpiste  fresh ski tracks in untouched powder
    mountain  ridges only
  No animation. Colours come from the --banner-* tokens (light and dark).
-->
<script lang="ts">
  import type { BannerScene } from '../tiles/options';

  let { scene = 'mountain', skyline = [] }: { scene?: BannerScene; skyline?: number[] } =
    $props();

  const uid = $props.id();
  const W = 400;
  const H = 150;
  const FALLBACK = [0.35, 0.6, 0.45, 0.8, 0.55, 0.7, 0.4];

  /** Rugged ridge through the points, closed along the bottom edge. */
  function ridge(points: number[], base: number, amplitude: number): string {
    const values = points.length >= 2 ? points : FALLBACK;
    const coords = values.map((v, i): [number, number] => [
      (i / (values.length - 1)) * W,
      H - (base + v * amplitude),
    ]);
    let d = `M0 ${H} L${coords[0]![0]} ${coords[0]![1].toFixed(1)}`;
    for (let i = 1; i < coords.length; i++) {
      const [x0, y0] = coords[i - 1]!;
      const [x1, y1] = coords[i]!;
      const sx = x0 + (x1 - x0) * (i % 2 ? 0.38 : 0.62);
      const sy = Math.max(y0, y1) - Math.abs(y1 - y0) * 0.35 + 4;
      d += ` L${sx.toFixed(1)} ${sy.toFixed(1)} L${x1.toFixed(1)} ${y1.toFixed(1)}`;
    }
    return `${d} L${W} ${H} Z`;
  }

  const far = $derived(ridge(skyline, 46, 70));
  const near = $derived(
    ridge(
      [...(skyline.length >= 2 ? skyline : FALLBACK)].reverse().map((v) => 0.2 + v * 0.5),
      8,
      62,
    ),
  );

  // Deterministic flake positions (x, y, radius).
  const flakes = Array.from({ length: 34 }, (_, i) => ({
    x: (i * 83.7) % W,
    y: ((i * 47.3) % 112) + 4,
    r: i % 6 === 0 ? 2.4 : i % 3 === 0 ? 1.7 : 1.2,
  }));

  /** Six-branch snowflake glyph centred on (x, y) with radius s. */
  function glyph(x: number, y: number, s: number): string {
    const dx = s * 0.87;
    const dy = s / 2;
    return `M${x} ${y - s}V${y + s}M${x - dx} ${y - dy}L${x + dx} ${y + dy}M${x - dx} ${y + dy}L${x + dx} ${y - dy}`;
  }
  const glyphs = [glyph(64, 30, 7), glyph(218, 52, 9), glyph(350, 26, 6)];

  // Groomed piste: a band widening downhill (perspective) between two cubic
  // Bézier edges. Corduroy lines follow the fall line, like a groomer's tracks.
  type Pt = [number, number];
  const LEFT: Pt[] = [[215, 70], [198, 95], [246, 112], [226, 150]];
  const RIGHT: Pt[] = [[237, 70], [222, 95], [298, 112], [286, 150]];
  const mix = (a: Pt, b: Pt, t: number): Pt => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  const curve = (p: Pt[]) =>
    `M${p[0]![0]} ${p[0]![1]} C${p[1]![0]} ${p[1]![1]}, ${p[2]![0]} ${p[2]![1]}, ${p[3]![0]} ${p[3]![1]}`;
  const pisteShape =
    curve(LEFT) +
    ` L${RIGHT[3]![0]} ${RIGHT[3]![1]} C${RIGHT[2]![0]} ${RIGHT[2]![1]}, ${RIGHT[1]![0]} ${RIGHT[1]![1]}, ${RIGHT[0]![0]} ${RIGHT[0]![1]} Z`;
  const corduroy = [0.2, 0.4, 0.6, 0.8].map((t) =>
    curve(LEFT.map((point, i) => mix(point, RIGHT[i]!, t))),
  );
  const poles = [
    { x: 211, y: 94 },
    { x: 266, y: 94 },
    { x: 222, y: 122 },
    { x: 292, y: 122 },
  ];

  // Off-piste: powder sprayed at the end of the tracks.
  const puffs = [
    { x: 182, y: 146, r: 3 },
    { x: 190, y: 140, r: 2 },
    { x: 174, y: 140, r: 2.4 },
    { x: 244, y: 146, r: 2.6 },
    { x: 252, y: 141, r: 1.8 },
  ];
</script>

<svg class="art" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <linearGradient id="{uid}-sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" style="stop-color: var(--banner-sky-top)" />
      <stop offset="1" style="stop-color: var(--banner-sky-bottom)" />
    </linearGradient>
    <linearGradient id="{uid}-snow" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" style="stop-color: var(--banner-ridge-near)" />
      <stop offset="1" style="stop-color: var(--banner-ridge-shade)" />
    </linearGradient>
  </defs>

  <rect width={W} height={H} fill="url(#{uid}-sky)" />
  {#if scene !== 'snowfall'}
    <circle cx="342" cy="64" r="13" style="fill: var(--banner-sun)" opacity="0.9" />
  {/if}
  <path d={far} style="fill: var(--banner-ridge-far)" />
  <path d={near} fill="url(#{uid}-snow)" />

  {#if scene === 'snowfall'}
    <g style="fill: var(--banner-sun)">
      {#each flakes as flake, i (i)}
        <circle cx={flake.x} cy={flake.y} r={flake.r} opacity={0.55 + (i % 4) * 0.12} />
      {/each}
    </g>
    <g style="stroke: var(--banner-sun)" stroke-width="1.6" stroke-linecap="round" opacity="0.9">
      {#each glyphs as d (d)}
        <path {d} />
      {/each}
    </g>
  {:else if scene === 'piste'}
    <path d={pisteShape} style="fill: var(--banner-ridge-near)" />
    <g fill="none" style="stroke: var(--banner-ridge-shade)" stroke-width="0.9">
      {#each corduroy as d (d)}
        <path {d} />
      {/each}
    </g>
    <g style="fill: var(--banner-detail)">
      {#each poles as pole, i (i)}
        <rect x={pole.x} y={pole.y} width="2.4" height="15" rx="1" />
      {/each}
    </g>
  {:else if scene === 'offpiste'}
    <g
      fill="none"
      style="stroke: var(--banner-detail)"
      stroke-width="1.6"
      stroke-linecap="round"
      opacity="0.75"
    >
      <path d="M150 74 C 176 88, 128 100, 160 114 S 150 138, 178 150" />
      <path d="M157 74 C 183 88, 135 100, 167 114 S 157 138, 185 150" />
      <path d="M262 80 C 240 96, 288 108, 258 124 S 270 142, 248 150" />
    </g>
    <g style="fill: var(--banner-ridge-near)">
      {#each puffs as puff, i (i)}
        <circle cx={puff.x} cy={puff.y} r={puff.r} />
      {/each}
    </g>
  {/if}
</svg>

<style>
  .art {
    display: block;
    width: 100%;
    height: 100%;
  }
</style>
