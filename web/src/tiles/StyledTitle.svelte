<!--
  Styled title of a `full` tile (tile `title_style`, lib/titleStyles.ts,
  TILES.md §3). The text stays a plain text node of the tile's <h2> (screen
  readers, translation, search); the style only changes its font and adds
  decorations hidden from assistive technologies.

  Fallback: until the style's font has loaded, or if it never does (slow or
  no network, blocked font, no font loading API), the standard title shows
  (the tile's usual Sora title), so the tile never waits on it.

  sunrise (Bluebird): Righteous with warm stacked shadows, and a sun rising
  behind the word in an 8 s loop; the sun only moves (transform, opacity),
  pauses off screen and while the card is turned, and stands still with
  reduced motion.

  danger_sign (avalanche danger): the title on a yellow mountain danger sign
  tilted by -4deg, in Oswald capitals on two lines (`splitSignTitle`: "RISQUE
  D'" small, "AVALANCHE" large), two steel bolts, and a white glint sliding
  over the sheet every 4 s (same pause and reduced-motion rules: no glint).
-->
<script lang="ts">
  import { type StyleId, splitSignTitle, titleFontReady } from '../lib/titleStyles';

  let { style, text }: { style: StyleId; text: string } = $props();

  const lines = $derived(splitSignTitle(text));
  let ready = $state(false);
  let visible = $state(true);
  let element = $state<HTMLSpanElement>();

  $effect(() => {
    let alive = true;
    void titleFontReady(style, text).then((ok) => {
      if (alive) ready = ok;
    });
    return () => {
      alive = false;
    };
  });

  // Pause the decoration while the tile is off screen.
  $effect(() => {
    if (!element || typeof IntersectionObserver === 'undefined') return;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry) visible = entry.isIntersecting;
    });
    observer.observe(element);
    return () => observer.disconnect();
  });
</script>

{#if ready}
  <span class="styled {style}" class:paused={!visible} bind:this={element}>
    {#if style === 'sunrise'}
      <span class="sun" aria-hidden="true"></span>
      <span class="text">{text}</span>
    {:else if style === 'danger_sign'}
      <span class="sign">
        <i class="bolt left" aria-hidden="true"></i><i class="bolt right" aria-hidden="true"></i>
        {#if lines[0]}<span class="small">{lines[0]}</span>{/if}<span class="large">{lines[1]}</span>
        <i class="glint" aria-hidden="true"></i>
      </span>
    {/if}
  </span>
{:else}
  {text}
{/if}

<style>
  .styled {
    position: relative;
    display: inline-grid;
    place-items: center;
    isolation: isolate;
    vertical-align: middle;
  }

  /* --------------------------------------------------------------- sunrise */
  .sunrise .text {
    font-family: var(--font-title-sunrise);
    font-weight: 400;
    font-size: 2.6rem;
    line-height: 1.15;
    letter-spacing: 0.01em;
    text-shadow:
      2px 2px 0 var(--title-sunrise-1),
      4px 4px 0 var(--title-sunrise-2),
      6px 6px 0 var(--title-sunrise-3),
      8px 8px 10px var(--title-sunrise-shade);
  }

  .sun {
    position: absolute;
    z-index: -1;
    left: 50%;
    top: 50%;
    width: 6.5rem;
    aspect-ratio: 1;
    margin: -3.25rem 0 0 -3.25rem;
    border-radius: 50%;
    background: radial-gradient(
      circle,
      var(--title-sun-core) 0 26%,
      var(--title-sun-glow) 42%,
      var(--title-sun-halo) 60%,
      transparent 70%
    );
    animation: rise 8s ease-in-out infinite;
  }

  @keyframes rise {
    0% {
      transform: translateY(3rem) scale(0.6);
      opacity: 0;
    }
    30%,
    70% {
      transform: translateY(-0.9rem) scale(1);
      opacity: 1;
    }
    100% {
      transform: translateY(-1.8rem) scale(1.05);
      opacity: 0;
    }
  }

  /* ----------------------------------------------------------- danger_sign */
  .sign {
    position: relative;
    display: inline-grid;
    justify-items: center;
    gap: 2px;
    overflow: hidden;
    padding: 8px 18px 7px;
    border: 3px solid var(--title-sign-ink);
    border-radius: 7px;
    background: var(--title-sign-bg);
    color: var(--title-sign-ink);
    font-family: var(--font-title-sign);
    font-weight: 700;
    line-height: 1;
    text-transform: uppercase;
    text-shadow: none;
    white-space: nowrap;
    box-shadow: 0 5px 12px var(--title-sign-shade);
    transform: rotate(-4deg);
  }

  .small {
    font-size: 1rem;
    letter-spacing: 0.1em;
  }

  .large {
    font-size: 2.3rem;
    letter-spacing: 0.01em;
  }

  .bolt {
    position: absolute;
    top: 5px;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, var(--title-sign-bolt-hi), var(--title-sign-bolt));
  }

  .bolt.left {
    left: 6px;
  }

  .bolt.right {
    right: 6px;
  }

  .glint {
    position: absolute;
    inset: -20% -60%;
    background: linear-gradient(105deg, transparent 42%, var(--title-sign-glint) 50%, transparent 58%);
    transform: translateX(-60%);
    animation: glint 4s ease-in-out infinite;
    pointer-events: none;
  }

  @keyframes glint {
    0% {
      transform: translateX(-60%);
    }
    50%,
    100% {
      transform: translateX(60%);
    }
  }

  .paused .sun,
  .paused .glint,
  :global(.flipper.flipped) .sun,
  :global(.flipper.flipped) .glint {
    animation-play-state: paused;
  }

  @media (prefers-reduced-motion: reduce) {
    .sun {
      animation: none;
      transform: translateY(-0.9rem);
      opacity: 1;
    }

    .glint {
      animation: none;
      opacity: 0;
    }
  }
</style>
