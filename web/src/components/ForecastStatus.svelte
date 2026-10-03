<!-- Forecast date and update time, shown on the sky above the tiles. -->
<script lang="ts">
  import { type MassifDaily, todayIn } from '../lib/data';
  import { formatLongDate, formatTime } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import Icon from './Icon.svelte';

  let { data }: { data: MassifDaily } = $props();

  const stale = $derived(data.forecast_date !== todayIn(data.timezone));
  const date = $derived(formatLongDate(data.forecast_date, i18n.locale));
</script>

<div class="status">
  <p class="date">{i18n.t('status.forecastFor', { date })}</p>
  <p class="updated tabular">
    {i18n.t('status.updatedAt', {
      time: formatTime(data.generated_at, i18n.locale, data.timezone),
    })}
  </p>
  {#if stale}
    <p class="stale glass" role="status">
      <Icon name="info" size={18} />
      <span>{i18n.t('status.stale', { date })}</span>
    </p>
  {/if}
</div>

<style>
  .status {
    display: grid;
    gap: 2px;
    padding: 18px 4px 14px;
    color: var(--ink-on-sky);
  }

  .date {
    font-size: 1.375rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.2;
  }

  .date::first-letter {
    text-transform: uppercase;
  }

  .updated {
    font-size: 0.875rem;
    color: var(--ink-on-sky-soft);
  }

  .stale {
    display: flex;
    gap: 8px;
    align-items: flex-start;
    margin-top: 10px;
    padding: 10px 12px;
    border-radius: var(--radius-m);
    color: var(--ink);
    font-size: 0.8125rem;
  }
</style>
