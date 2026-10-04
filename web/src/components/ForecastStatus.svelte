<!--
  Dark-blue strip above the tiles (where betting apps show their promo
  banner): date and time of the last refresh, and a notice when it is older
  than expected (refreshes run every 6 hours).
-->
<script lang="ts">
  import { type MassifDaily, todayIn } from '../lib/data';
  import { formatLongDate, formatTime } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import Icon from './Icon.svelte';

  let {
    data,
    massifName = '',
    now,
  }: { data: MassifDaily; massifName?: string; now: number } = $props();

  /** A refresh every 6 hours, plus margin for late GitHub Actions runs. */
  const STALE_AFTER_MS = 7 * 3600_000;

  const stale = $derived(now - Date.parse(data.generated_at) > STALE_AFTER_MS);
  const date = $derived(
    formatLongDate(todayIn(data.timezone, new Date(data.generated_at)), i18n.locale),
  );
</script>

<div class="status" role="status">
  <div class="text">
    {#if massifName}<p class="massif">{massifName}</p>{/if}
    <p class="date">{i18n.t('status.forecastFor', { date })}</p>
    <p class="updated tabular">
      {i18n.t('status.updatedAt', {
        time: formatTime(data.generated_at, i18n.locale, data.timezone),
      })}
    </p>
    {#if stale}
      <p class="stale">
        <Icon name="info" size={16} />
        <span>{i18n.t('status.stale', { date })}</span>
      </p>
    {/if}
  </div>
  <span class="flake" aria-hidden="true"><Icon name="snowflake" size={44} /></span>
</div>

<style>
  .status {
    position: relative;
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 14px 0 16px;
    padding: 14px 16px;
    overflow: hidden;
    border-radius: var(--radius-l);
    background: var(--status-bg);
    color: var(--status-ink);
  }

  .text {
    display: grid;
    gap: 2px;
    min-width: 0;
  }

  .massif {
    font-size: 0.6875rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--sky);
  }

  .date {
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-weight: 800;
    font-style: italic;
    line-height: 1.1;
  }

  .date::first-letter {
    text-transform: uppercase;
  }

  .updated {
    font-size: 0.8125rem;
    color: var(--status-soft);
  }

  .stale {
    display: flex;
    gap: 6px;
    align-items: flex-start;
    margin-top: 6px;
    font-size: 0.8125rem;
    color: var(--status-soft);
  }

  .flake {
    flex: none;
    margin-left: auto;
    color: var(--sky);
    opacity: 0.9;
  }
</style>
