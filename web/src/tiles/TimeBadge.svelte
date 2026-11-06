<!--
  Time badge of a tile of live KPIs (TILES.md §5 and §9): a small
  rectangular ticket, "Dem. | Matin".
    - Day cell: short label of the day in its dark colour (`when`: today,
      tonight, tomorrow), white text.
    - Moment cell, soft: the colour of the period `tone` at 24 % over the
      card with its text colour, or at 42 % over dark glass on an image with
      white text; an icon repeats the colour.
  A whole day shows the day alone ("Auj."); tonight shows "Cette nuit" alone,
  with a moon. Rectangular on purpose, against the round pills and badges.

  Hidden from screen readers: the tile title carries the period in words
  (lib/periods.ts `TileTime.label`).
-->
<script lang="ts">
  import Icon from '../components/Icon.svelte';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { TONE_ICONS, type TileTime } from '../lib/periods';

  let { time, onImage = false }: { time: TileTime; onImage?: boolean } = $props();
</script>

<span class="ticket" class:on-image={onImage} data-when={time.when} aria-hidden="true">
  <span class="day">
    {#if time.when === 'tonight'}<Icon name="moon" size={12} />{/if}
    {i18n.pick(time.day)}
  </span>
  {#if time.moment && time.tone}
    <span class="moment" data-tone={time.tone}>
      <Icon name={TONE_ICONS[time.tone]} size={12} />
      <span class="text">{i18n.pick(time.moment)}</span>
    </span>
  {/if}
</span>

<style>
  .ticket {
    display: inline-flex;
    align-items: stretch;
    max-width: 100%;
    height: 1.375rem;
    border-radius: 5px;
    overflow: hidden;
    font-size: 0.625rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    line-height: 1;
    text-transform: uppercase;
    white-space: nowrap;
  }

  [data-when='today'] {
    --w: var(--when-today);
  }
  [data-when='tonight'] {
    --w: var(--when-tonight);
  }
  [data-when='tomorrow'] {
    --w: var(--when-tomorrow);
  }

  [data-tone='morning'] {
    --t-bg: var(--tone-morning-bg);
    --t-text: var(--tone-morning-text);
    --t-vivid: var(--tone-morning-vivid);
  }
  [data-tone='midday'] {
    --t-bg: var(--tone-midday-bg);
    --t-text: var(--tone-midday-text);
    --t-vivid: var(--tone-midday-vivid);
  }
  [data-tone='afternoon'] {
    --t-bg: var(--tone-afternoon-bg);
    --t-text: var(--tone-afternoon-text);
    --t-vivid: var(--tone-afternoon-vivid);
  }
  [data-tone='evening'] {
    --t-bg: var(--tone-evening-bg);
    --t-text: var(--tone-evening-text);
    --t-vivid: var(--tone-evening-vivid);
  }
  [data-tone='night'] {
    --t-bg: var(--tone-night-bg);
    --t-text: var(--tone-night-text);
    --t-vivid: var(--tone-night-vivid);
  }

  .day,
  .moment {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    min-width: 0;
    padding: 0 6px;
  }

  .day {
    flex: none;
    background: color-mix(in srgb, var(--w) 88%, var(--surface));
    color: var(--when-ink);
  }

  .moment {
    background: color-mix(in srgb, var(--t-bg) 24%, var(--surface));
    color: var(--t-text);
  }

  .ticket :global(svg) {
    flex: none;
  }

  /* line-height above 1: `overflow: hidden` would clip the accents of
     capitals (MAÑ., APRÈM). */
  .text {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.4;
  }

  /* On a tile image: glass tinted by the colours, white text, vivid icon. */
  .on-image .day {
    background: color-mix(in srgb, var(--w) 80%, transparent);
    -webkit-backdrop-filter: blur(8px);
    backdrop-filter: blur(8px);
  }

  .on-image .moment {
    background: color-mix(in srgb, var(--t-bg) 42%, var(--ticket-glass));
    color: var(--ticket-glass-ink);
    -webkit-backdrop-filter: blur(8px);
    backdrop-filter: blur(8px);
  }

  .on-image .moment :global(svg) {
    color: var(--t-vivid);
  }

  @media (prefers-reduced-transparency: reduce) {
    .on-image .day {
      background: var(--w);
    }

    .on-image .moment {
      background: color-mix(in srgb, var(--t-bg) 42%, var(--when-today));
    }

    .on-image .day,
    .on-image .moment {
      -webkit-backdrop-filter: none;
      backdrop-filter: none;
    }
  }
</style>
