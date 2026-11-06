<!--
  Two-sided card used by every tile type.
    - Front: the tile, with a "?" button in the top-right corner.
    - Back: details about the KPI (KpiBack), with a "×" button to return.
  Tapping or clicking the card anywhere also flips it, except on interactive
  elements (odds buttons, station rows, "see all", links) and on station
  details. The hidden side is inert, so keyboard focus never reaches it.
  The back has the height of the front and scrolls when its content is longer.
  Each face carries its own glass card, so the card turns with it and its
  corners always match the card edges.
  Mirror-free turn: the faces swap at mid-turn (card edge-on), by a delayed
  `visibility` switch timed with a symmetric easing, instead of relying on
  `backface-visibility`, which mobile browsers ignore on glass surfaces
  (`backdrop-filter`): the reversed front text never shows, in either
  direction.
  `plain`: the front has no image behind the "?" button (TileCompact), which
  then takes the plain style of the back's "×" button.
  `theme`: colour theme of the card (token overrides `[data-tile-theme]` in
  styles/base.css), e.g. `rewind` for the Rewind tiles.
-->
<script lang="ts">
  import { tick, type Snippet } from 'svelte';
  import Icon from '../components/Icon.svelte';
  import { i18n } from '../lib/i18n/i18n.svelte';

  let {
    labelledby,
    front,
    back,
    plain = false,
    theme = 'default',
  }: {
    labelledby: string;
    front: Snippet;
    back: Snippet;
    plain?: boolean;
    theme?: string;
  } = $props();

  let flipped = $state(false);
  let backScroll = $state<HTMLElement>();
  let backHasMore = $state(false);

  /** Fade the bottom of the back while part of its content is still hidden. */
  function updateBackFade() {
    if (!backScroll) return;
    backHasMore = backScroll.scrollTop + backScroll.clientHeight < backScroll.scrollHeight - 4;
  }

  $effect(() => {
    if (flipped) updateBackFade();
  });
  let infoButton = $state<HTMLButtonElement>();
  let closeButton = $state<HTMLButtonElement>();

  const NO_FLIP = 'button, a, input, select, textarea, label, [data-no-flip]';

  async function toggle() {
    flipped = !flipped;
    await tick();
    (flipped ? closeButton : infoButton)?.focus({ preventScroll: true });
  }

  function onFaceClick(event: MouseEvent) {
    const target = event.target as Element | null;
    if (target?.closest(NO_FLIP)) return;
    if (window.getSelection()?.toString()) return; // the user is selecting text
    void toggle();
  }
</script>

<section
  class="flip-card"
  aria-labelledby={labelledby}
  data-tile-theme={theme === 'default' ? undefined : theme}
>
  <div class="flipper" class:flipped>
    <!-- Pointer convenience only: the "?" and "×" buttons are the keyboard path. -->
    <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
    <div class="face front card" class:plain inert={flipped} onclick={onFaceClick}>
      <div class="card-body">
        {@render front()}
        <button
          bind:this={infoButton}
          type="button"
          class="flip-button"
          aria-label={i18n.t('tile.info')}
          aria-expanded={flipped}
          onclick={toggle}
        >
          ?
        </button>
      </div>
    </div>
    <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
    <div class="face back card" inert={!flipped} onclick={onFaceClick}>
      <div class="card-body">
        <div
          bind:this={backScroll}
          class="back-scroll"
          class:has-more={backHasMore}
          onscroll={updateBackFade}
        >
          {@render back()}
        </div>
        <button
          bind:this={closeButton}
          type="button"
          class="flip-button"
          aria-label={i18n.t('tile.infoClose')}
          onclick={toggle}
        >
          <Icon name="close" size={18} />
        </button>
      </div>
    </div>
  </div>
</section>

<style>
  .flip-card {
    --flip-duration: 0.55s;
    perspective: 1600px;
  }

  /* Symmetric easing: half the time = half the turn (90°, edge-on). */
  .flipper {
    position: relative;
    transform-style: preserve-3d;
    transition: transform var(--flip-duration) cubic-bezier(0.45, 0, 0.55, 1);
  }

  .flipper.flipped {
    transform: rotateY(180deg);
  }

  /* The faces swap exactly at mid-turn, both ways: the hidden one is never
     drawn, even where backface-visibility is ignored (glass surfaces). */
  .face {
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
    cursor: pointer;
    transition: visibility 0s linear calc(var(--flip-duration) / 2);
  }

  .front,
  .flipped .back {
    visibility: visible;
  }

  .back,
  .flipped .front {
    visibility: hidden;
  }

  /* Same box as the front, turned to face backwards. */
  .back {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    transform: rotateY(180deg);
  }

  .back > .card-body {
    flex: 1;
    min-height: 0;
  }

  .back-scroll {
    height: 100%;
    overflow-y: auto;
    overscroll-behavior: contain;
    scrollbar-width: thin;
    scrollbar-color: var(--line) transparent;
  }

  .back-scroll.has-more {
    -webkit-mask-image: linear-gradient(180deg, #000 82%, transparent);
    mask-image: linear-gradient(180deg, #000 82%, transparent);
  }

  .flip-button {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 3;
    display: grid;
    place-items: center;
    width: 2.25rem;
    height: 2.25rem;
    border-radius: 50%;
    /* Glass button on the image. */
    border: 1px solid rgba(255, 255, 255, 0.5);
    background: rgba(255, 255, 255, 0.2);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);
    color: #ffffff;
    font-family: var(--font-display);
    letter-spacing: var(--display-tracking);
    font-size: 1.125rem;
    font-weight: var(--display-weight);
    line-height: 1;
    cursor: pointer;
    -webkit-backdrop-filter: blur(10px);
    backdrop-filter: blur(10px);
  }

  .back .flip-button,
  .plain .flip-button {
    border-color: var(--pill-border);
    background: var(--pill-bg);
    box-shadow: none;
    color: var(--pill-ink);
  }

  @media (prefers-reduced-transparency: reduce) {
    .flip-button {
      background: var(--banner-label-bg);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .flipper,
    .face {
      transition: none;
    }
  }
</style>
