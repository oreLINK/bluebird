<!--
  Bluebird mark: a toric ski goggle seen three-quarters, strap going back on
  the right, a small glare at the top left of the lens. Only the lens
  gradient changes with the phase of the day (lib/timeOfDay.ts); frame and
  strap use --logo-frame, the glare --logo-glare. The static copies of the
  `day` version are web/public/favicon.svg and the home-screen icon
  (web/scripts/apple-touch-icon.svg → web/public/apple-touch-icon.png): keep
  the paths below in sync with them.
-->
<script lang="ts">
  import type { DayPhase } from '../lib/timeOfDay';

  let { phase = 'day' }: { phase?: DayPhase } = $props();

  /** Unique gradient id: several inline SVGs share the document id space. */
  const uid = $props.id();
  const lensId = `logo-lens-${uid}`;
</script>

<svg class="mark" viewBox="0 0 64 64" aria-hidden="true" focusable="false">
  <defs>
    <linearGradient id={lensId} x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" style="stop-color: var(--logo-lens-{phase}-1)" />
      <stop offset="0.5" style="stop-color: var(--logo-lens-{phase}-2)" />
      <stop offset="1" style="stop-color: var(--logo-lens-{phase}-3)" />
    </linearGradient>
  </defs>
  <path class="frame" d="M57 21L63.5 19V40L57 41Z" />
  <path
    class="frame"
    d="M3 25C3 17 9 13 18 13H43C50 13 55 15 57 19L60 22V38L57 41C55 46 51 48 45 48H38C34.5 48 33 42.5 29.5 42.5C26 42.5 25 48 21 48H12C6 48 3 44 3 38Z"
  />
  <path
    d="M7 25.5C7 20 11 17.5 18 17.5H43C48 17.5 51.5 19 53 22L55.5 24V36.5L53 38.5C51.5 42 49 43.5 45 43.5H38.5C35.5 43.5 33.5 38 29.5 38C25.5 38 24.5 43.5 21 43.5H12.5C9 43.5 7 41 7 37.5Z"
    style="fill: url(#{lensId})"
  />
  <path class="glare" d="M12 25C15 21.5 22 20 30 20" />
</svg>

<style>
  .mark {
    display: block;
    width: 100%;
    height: 100%;
    overflow: visible;
  }

  .frame {
    fill: var(--logo-frame);
  }

  .glare {
    fill: none;
    stroke: var(--logo-glare);
    stroke-width: 2.6;
    stroke-linecap: round;
    opacity: 0.75;
  }

  stop {
    transition: stop-color 1.2s ease;
  }

  @media (prefers-reduced-motion: reduce) {
    stop {
      transition: none;
    }
  }

  @media (forced-colors: active) {
    .frame {
      fill: CanvasText;
    }
  }
</style>
