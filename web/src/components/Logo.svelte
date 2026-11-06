<!--
  Bluebird logo: the ski goggle mark (LogoMark.svelte) followed by the
  wordmark, two-tone italic display type, "bird" with a light-blue gradient
  and a short underline swoosh. The lens gradient follows the phase of the
  day (dawn, day, dusk, night: lib/timeOfDay.ts) in the timezone of the
  first massif, checked every minute. The favicon and the home-screen icon
  are static copies of the `day` mark.
-->
<script lang="ts">
  import { massifs } from '../lib/config';
  import { dayPhase } from '../lib/timeOfDay';
  import LogoMark from './LogoMark.svelte';

  /** Logo height scale: 1 is the header size. */
  let { scale = 1 }: { scale?: number } = $props();

  const timezone = massifs[0]?.timezone ?? 'UTC';
  let now = $state(new Date());
  const phase = $derived(dayPhase(now, timezone));

  $effect(() => {
    const timer = setInterval(() => (now = new Date()), 60_000);
    return () => clearInterval(timer);
  });
</script>

<span class="logo" style="--scale: {scale}">
  <span class="mark"><LogoMark {phase} /></span>
  <span class="wordmark"><span class="a">Blue</span><span class="b">bird</span></span>
</span>

<style>
  .logo {
    display: inline-flex;
    align-items: center;
    gap: calc(0.375rem * var(--scale, 1));
    min-width: 0;
  }

  .mark {
    flex: none;
    width: calc(2.875rem * var(--scale, 1));
    height: calc(2.875rem * var(--scale, 1));
  }

  .wordmark {
    display: inline-block;
    font-family: var(--font-logo);
    font-size: calc(2.375rem * var(--scale, 1));
    font-style: italic;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.025em;
    /* Room for the italic overhang of the last letter. */
    padding-right: 0.08em;
  }

  .a {
    color: var(--logo-a);
  }

  .b {
    position: relative;
    color: var(--logo-b);
    background: linear-gradient(100deg, var(--logo-b) 20%, var(--sky));
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .b::after {
    content: '';
    position: absolute;
    left: 0.06em;
    right: 0.02em;
    bottom: -0.1em;
    height: 0.1em;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--logo-b), var(--sky));
    transform: skewX(-18deg);
  }

  @media (forced-colors: active) {
    .b {
      -webkit-text-fill-color: currentColor;
    }
  }
</style>
