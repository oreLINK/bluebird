<!--
  Explanatory details of one station for one KPI: time window (when it differs
  between stations), the drivers declared in config/kpis.yaml, confidence and
  elevation. Shared by every tile type.
-->
<script lang="ts">
  import ConfidenceDots from '../components/ConfidenceDots.svelte';
  import type { Kpi } from '../lib/config';
  import type { RankingEntry, StationInfo } from '../lib/data';
  import { formatDriver, formatWindow } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';

  let {
    id,
    entry,
    kpi,
    station,
    timezone,
    showWindow = false,
  }: {
    id: string;
    entry: RankingEntry;
    kpi: Kpi | undefined;
    station: StationInfo | undefined;
    timezone: string;
    showWindow?: boolean;
  } = $props();

  const drivers = $derived(
    Object.entries(kpi?.drivers ?? {}).flatMap(([key, spec]) => {
      const value = formatDriver(entry.drivers[key], i18n.locale, spec.unit, spec.decimals ?? 0);
      return value === null ? [] : [{ key, label: i18n.pick(spec.label), value }];
    }),
  );
</script>

<dl class="details" {id} data-no-flip>
  {#if showWindow}
    <div>
      <dt>{i18n.t('tile.window')}</dt>
      <dd class="tabular">
        {formatWindow(entry.window_start, entry.window_end, i18n.locale, timezone)}
      </dd>
    </div>
  {/if}
  {#each drivers as driver (driver.key)}
    <div>
      <dt>{driver.label}</dt>
      <dd class="tabular">{driver.value}</dd>
    </div>
  {/each}
  <div>
    <dt>{i18n.t('tile.confidence')}</dt>
    <dd>
      <ConfidenceDots level={entry.confidence} />
      {i18n.t(`confidence.${entry.confidence}`)}
    </dd>
  </div>
  {#if station}
    <div>
      <dt>{i18n.t('tile.elevation')}</dt>
      <dd class="tabular">{station.elevation.base}–{station.elevation.summit}&#8239;m</dd>
    </div>
  {/if}
</dl>

<style>
  .details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(7.5rem, 1fr));
    gap: 10px 14px;
    margin: 0;
    padding: 12px 14px;
    border-radius: var(--radius-m);
    background: var(--surface-2);
    border: 1px solid var(--line);
    font-size: 0.8125rem;
  }

  dt {
    color: var(--ink-faint);
  }

  dd {
    margin: 2px 0 0;
    font-weight: 600;
  }

  dd :global(.dots) {
    margin-right: 6px;
  }
</style>
