<!--
  Small national flag for a language (LOCALE_FLAGS in lib/i18n/core.ts:
  France, United Kingdom, Spain),
  drawn in SVG rather than with emoji: emoji flags show as two letters on
  Windows. Colours are the --flag-* tokens of styles/tokens.css (set with
  `style`, since var() does not work in SVG presentation attributes).
  Decorative: the button or option that holds it names the language.
-->
<script lang="ts">
  import type { FlagCountry } from '../lib/i18n/core';

  let { country, width = 26 }: { country: FlagCountry; width?: number } = $props();
</script>

<span class="flag" style="width: {width}px; height: {Math.round((width * 2) / 3)}px">
  {#if country === 'fr'}
    <svg viewBox="0 0 3 2" preserveAspectRatio="none" aria-hidden="true" focusable="false">
      <rect width="1" height="2" style="fill: var(--flag-fr-blue)" />
      <rect x="1" width="1" height="2" style="fill: var(--flag-white)" />
      <rect x="2" width="1" height="2" style="fill: var(--flag-fr-red)" />
    </svg>
  {:else if country === 'es'}
    <!-- Civil flag (no coat of arms): red, yellow twice as tall, red. -->
    <svg viewBox="0 0 3 2" preserveAspectRatio="none" aria-hidden="true" focusable="false">
      <rect width="3" height="2" style="fill: var(--flag-es-red)" />
      <rect y="0.5" width="3" height="1" style="fill: var(--flag-es-yellow)" />
    </svg>
  {:else}
    <svg viewBox="0 0 60 30" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
      <rect width="60" height="30" style="fill: var(--flag-gb-blue)" />
      <path d="M0 0L60 30M60 0L0 30" style="stroke: var(--flag-white); stroke-width: 6" />
      <path d="M0 0L60 30M60 0L0 30" style="stroke: var(--flag-gb-red); stroke-width: 2" />
      <path d="M30 0V30M0 15H60" style="stroke: var(--flag-white); stroke-width: 10" />
      <path d="M30 0V30M0 15H60" style="stroke: var(--flag-gb-red); stroke-width: 6" />
    </svg>
  {/if}
</span>

<style>
  .flag {
    display: block;
    flex: none;
    overflow: hidden;
    border-radius: 4px;
    /* Keeps the white parts visible on a white surface. */
    box-shadow: inset 0 0 0 1px var(--line);
  }

  svg {
    display: block;
    width: 100%;
    height: 100%;
  }

  @media (forced-colors: active) {
    .flag {
      outline: 1px solid CanvasText;
    }
  }
</style>
