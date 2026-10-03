<!--
  Light falling-snow ambience. Density follows `intensity` (0..1), the best
  snowfall probability of the day. Hidden when the user prefers reduced motion.
-->
<script lang="ts">
  let { intensity = 0 }: { intensity?: number } = $props();

  /** Small deterministic PRNG so flakes don't jump on every re-render. */
  function random(seed: number): number {
    let t = (seed + 0x6d2b79f5) | 0;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  const count = $derived(Math.round(10 + 50 * Math.min(1, Math.max(0, intensity))));
  const flakes = $derived(
    Array.from({ length: count }, (_, i) => ({
      left: random(i * 4 + 1) * 100,
      size: 2 + random(i * 4 + 2) * 3.5,
      duration: 9 + random(i * 4 + 3) * 11,
      delay: -random(i * 4 + 4) * 20,
      drift: (random(i * 7) - 0.5) * 60,
      opacity: 0.45 + random(i * 9) * 0.5,
    })),
  );
</script>

<div class="snowfall" aria-hidden="true">
  {#each flakes as flake, i (i)}
    <span
      style="left: {flake.left}%; width: {flake.size}px; height: {flake.size}px;
        animation-duration: {flake.duration}s; animation-delay: {flake.delay}s;
        --drift: {flake.drift}px; opacity: {flake.opacity};"
    ></span>
  {/each}
</div>

<style>
  .snowfall {
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    overflow: hidden;
  }

  span {
    position: absolute;
    top: -12px;
    border-radius: 50%;
    background: var(--flake);
    filter: blur(0.3px);
    will-change: transform;
    animation-name: fall;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
  }

  @keyframes fall {
    from {
      transform: translate3d(0, -2vh, 0);
    }
    to {
      transform: translate3d(var(--drift), 104vh, 0);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .snowfall {
      display: none;
    }
  }
</style>
