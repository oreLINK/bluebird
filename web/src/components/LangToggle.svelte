<script lang="ts">
  import { LOCALES } from '../lib/i18n/core';
  import { i18n } from '../lib/i18n/i18n.svelte';
</script>

<div class="toggle glass glass-strong" role="group" aria-label={i18n.t('header.language')}>
  {#each LOCALES as locale (locale)}
    <button
      type="button"
      lang={locale}
      aria-pressed={i18n.locale === locale}
      onclick={() => i18n.setLocale(locale)}
    >
      {locale.toUpperCase()}
    </button>
  {/each}
</div>

<style>
  .toggle {
    display: inline-flex;
    padding: 3px;
    border-radius: 999px;
  }

  button {
    position: relative;
    min-width: 2.5rem;
    min-height: 2rem;
    padding: 0 0.6rem;
    border: 0;
    border-radius: 999px;
    background: transparent;
    color: var(--ink-soft);
    font-size: 0.8125rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    cursor: pointer;
  }

  button[aria-pressed='true'] {
    background: var(--accent);
    color: var(--accent-ink);
  }
</style>
