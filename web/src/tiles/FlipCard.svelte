<!--
  Two-sided card used by every tile type.
    - Front: the tile, with a "?" button in the top-right corner.
    - Back: details about the KPI (KpiBack), with a "×" button to return.
  Tapping or clicking the card anywhere also flips it, except on interactive
  elements (odds buttons, station rows, "see all", links) and on station
  details. The hidden side is inert, so keyboard focus never reaches it.
  The back has the height of the front and scrolls when its content is longer.
  Each face carries its own card frame (with the striped top corners), so the
  frame turns with the card and its corners always match the card edges.
-->
<script lang="ts">
  import { tick, type Snippet } from 'svelte';
  import Icon from '../components/Icon.svelte';
  import { i18n } from '../lib/i18n/i18n.svelte';

  let {
    labelledby,
    front,
    back,
  }: { labelledby: string; front: Snippet; back: Snippet } = $props();

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

<section class="flip-card" aria-labelledby={labelledby}>
  <div class="flipper" class:flipped>
    <!-- Pointer convenience only: the "?" and "×" buttons are the keyboard path. -->
    <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
    <div class="face front card" inert={flipped} onclick={onFaceClick}>
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
    perspective: 1600px;
  }

  .flipper {
    position: relative;
    transform-style: preserve-3d;
    transition: transform 0.55s cubic-bezier(0.2, 0.75, 0.25, 1);
  }

  .flipper.flipped {
    transform: rotateY(180deg);
  }

  .face {
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
    cursor: pointer;
  }

  /* Same box as the front (frame padding included), turned to face backwards. */
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
    width: 34px;
    height: 34px;
    border-radius: 50%;
    border: 1px solid rgba(255, 255, 255, 0.35);
    background: var(--banner-label-bg);
    color: #ffffff;
    font-family: var(--font-display);
    font-size: 1.125rem;
    font-style: italic;
    font-weight: 800;
    line-height: 1;
    cursor: pointer;
    -webkit-backdrop-filter: blur(6px);
    backdrop-filter: blur(6px);
  }

  .back .flip-button {
    border-color: var(--line);
    background: var(--surface-2);
    color: var(--ink);
  }

  @media (prefers-reduced-motion: reduce) {
    .flipper {
      transition: none;
    }
  }
</style>
