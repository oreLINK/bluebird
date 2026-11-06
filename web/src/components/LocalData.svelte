<!--
  Built-in page block `local_data` (config/pages.yaml, privacy page): lists the
  settings this site keeps in the browser's local storage (lib/prefs.ts) and
  deletes them on demand. Only the site's own `bluebird:` keys are removed;
  the page then reloads so every setting goes back to its default (language
  of the browser, System appearance, first massif, no filter).
-->
<script lang="ts">
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { clearPrefs, storedPrefs } from '../lib/prefs';

  const LABELS = {
    locale: 'localData.locale',
    theme: 'localData.theme',
    geo: 'localData.geo',
    filter: 'localData.filter',
  } as const;
  /** Delay before the reload, so the confirmation can be read. */
  const RELOAD_MS = 1800;

  let stored = $state(storedPrefs());
  let done = $state(false);

  const names = $derived([
    ...new Set(
      stored.map((key) => i18n.t(key in LABELS ? LABELS[key as keyof typeof LABELS] : 'localData.other')),
    ),
  ]);

  function clear() {
    clearPrefs();
    stored = [];
    done = true;
    setTimeout(() => window.location.reload(), RELOAD_MS);
  }
</script>

<div class="local-data">
  <p class="state" role="status">
    {#if done}
      {i18n.t('localData.done')}
    {:else if stored.length > 0}
      {i18n.t('localData.stored', { items: names.join(', ') })}
    {:else}
      {i18n.t('localData.empty')}
    {/if}
  </p>
  <button type="button" class="clear" onclick={clear} disabled={stored.length === 0}>
    {i18n.t('localData.clear')}
  </button>
</div>

<style>
  .local-data {
    display: grid;
    justify-items: start;
    gap: 10px;
  }

  .state {
    font-size: 0.9375rem;
    line-height: 1.55;
    color: var(--ink-soft);
  }

  .clear {
    min-height: 2.75rem;
    padding: 0 18px;
    border-radius: 999px;
    border: 1px solid var(--state-down-ink);
    background: var(--surface);
    color: var(--state-down-ink);
    font-size: 0.9375rem;
    font-weight: 600;
    cursor: pointer;
  }

  .clear:disabled {
    border-color: var(--line);
    color: var(--ink-faint);
    cursor: default;
  }
</style>
