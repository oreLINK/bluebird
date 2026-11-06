<!--
  LIVE badge in the top left corner of a `full` or `banner` tile: a real link
  to the official page of the leading station's webcam (new tab). Shown only
  when the tile's `webcam` rule holds (lib/webcams.ts); the webcam image itself
  is never displayed on the site. A link, so a tap on it never flips the card.
-->
<script lang="ts">
  import { i18n } from '../lib/i18n/i18n.svelte';
  import type { LiveWebcam } from '../lib/webcams';
  import Icon from './Icon.svelte';

  let { live, station }: { live: LiveWebcam; station: string } = $props();

  const PROVIDER_NAMES: Record<string, string> = { skaping: 'Skaping' };
  const label = $derived(
    i18n.t('webcam.open', {
      station,
      place: live.webcam.name,
      provider: PROVIDER_NAMES[live.webcam.provider] ?? live.webcam.provider,
    }),
  );
</script>

<a class="live" href={live.webcam.url} target="_blank" rel="noopener noreferrer" aria-label={label} title={label}>
  <span class="dot" aria-hidden="true"></span>
  <Icon name="webcam" size={14} />
  <span>{i18n.t('webcam.live')}</span>
</a>

<style>
  .live {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    height: 1.625rem;
    padding: 0 10px 0 8px;
    border-radius: 999px;
    background: var(--live-bg);
    color: var(--on-live);
    font-size: 0.6875rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    text-decoration: none;
    white-space: nowrap;
  }

  .live:focus-visible {
    outline: 2px solid var(--on-live);
    outline-offset: 2px;
  }

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
  }
</style>
