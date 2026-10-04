<!--
  One block of the "Service status" page (config/pages.yaml, `service_*`
  blocks), from diamond/status.json:
    service_summary     overall state, number of degraded items, refresh time
    service_sources     one line per data source (API)
    service_transforms  one line per transformation
    service_kpis        one line per indicator, with its degraded periods
    service_tiles       one line per tile of the current massif and period
  States carry an icon and a word, never colour alone. Periods already over
  are not listed.
-->
<script lang="ts" module>
  import type { ServiceStatus } from '../lib/data';

  export type ServiceBlock =
    | 'service_summary'
    | 'service_sources'
    | 'service_transforms'
    | 'service_kpis'
    | 'service_tiles';

  /** What the status blocks need: the status and where/when the visitor is. */
  export interface ServiceContext {
    status: ServiceStatus | null;
    massifId: string;
    timezone: string;
    now: number;
  }
</script>

<script lang="ts">
  import { kpis, sources, tiles } from '../lib/config';
  import { formatLongDate, formatTime } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { instanceTitle } from '../lib/periods';
  import {
    STATE_ICON,
    type StateId,
    type StatusPeriod,
    type StatusRow,
    periodLabel,
    statusView,
  } from '../lib/status';
  import Icon from './Icon.svelte';

  let { block, context }: { block: ServiceBlock; context: ServiceContext } = $props();

  const status = $derived(context.status);
  const view = $derived(status ? statusView(status, context.massifId, context.now) : null);

  const sourceName = (id: string) => sources.find((s) => s.id === id)?.attribution.name ?? id;
  const kpiName = (id: string) => i18n.pick(kpis.find((k) => k.id === id)?.name) || id;

  function periodText(period: StatusPeriod): string {
    if (!status) return period.key;
    return i18n.pick(periodLabel(status, period, context.timezone, context.now)) || period.key;
  }

  function tileName(tileId: string, period: StatusPeriod): string {
    const tile = tiles.find((t) => t.id === tileId);
    if (!tile || !status) return tileId;
    const label = periodLabel(status, period, context.timezone, context.now) ?? { fr: '', en: '' };
    const tileKpis = kpis.filter((k) => tile.kpis?.includes(k.id));
    return i18n.pick(instanceTitle(tile, tileKpis, label)).trim();
  }

  function detail(row: StatusRow): string {
    if (row.state === 'stale' && row.since) {
      return i18n.t('service.since', { time: formatTime(row.since, i18n.locale, context.timezone) });
    }
    if (row.state === 'partial' && row.expected) {
      return i18n.t('service.stations', { ok: row.ok ?? 0, expected: row.expected });
    }
    return '';
  }

  const rows = $derived.by((): { name: string; row: StatusRow; note?: string }[] => {
    if (!view) return [];
    switch (block) {
      case 'service_sources':
        return view.sources.map((row) => ({ name: sourceName(row.id), row }));
      case 'service_transforms':
        return view.transforms.map((row) => ({
          name: i18n.t('service.transformOf', { source: sourceName(row.id) }),
          row,
        }));
      case 'service_kpis':
        return view.kpis.map((row) => ({
          name: kpiName(row.id),
          row,
          note: (row.issues ?? [])
            .map((p) =>
              i18n.t('service.periodIssue', {
                period: periodText(p),
                state: i18n.t(`state.${p.state}`).toLowerCase(),
              }),
            )
            .join(' · '),
        }));
      case 'service_tiles':
        return view.tiles.map((row) => ({ name: tileName(row.tileId, row.period), row }));
      default:
        return [];
    }
  });

  const updated = $derived(
    status
      ? i18n.t('service.updated', {
          date: formatLongDate(
            new Intl.DateTimeFormat('en-CA', { timeZone: context.timezone }).format(
              new Date(status.generated_at),
            ),
            i18n.locale,
          ),
          time: formatTime(status.generated_at, i18n.locale, context.timezone),
        })
      : '',
  );
</script>

{#snippet pill(state: StateId, extra: string)}
  <span class="pill" data-state={state}>
    <Icon name={STATE_ICON[state]} size={14} />
    <span>{i18n.t(`state.${state}`)}{extra ? ` · ${extra}` : ''}</span>
  </span>
{/snippet}

{#if !status || !view}
  {#if block === 'service_summary'}
    <p class="summary">
      <span class="badge" data-state="down"><Icon name="alert" size={18} /></span>
      <span>{i18n.t('service.unavailable')}</span>
    </p>
  {/if}
{:else if block === 'service_summary'}
  <p class="summary">
    <span class="badge" data-state={view.state}>
      <Icon name={STATE_ICON[view.state]} size={18} />
    </span>
    <span class="summary-text">
      <strong>
        {view.degraded === 0
          ? i18n.t('service.allOk')
          : i18n.t('service.degraded', { count: view.degraded })}
      </strong>
      <span class="updated">{updated}</span>
    </span>
  </p>
{:else if rows.length}
  <ul class="rows">
    {#each rows as { name, row, note } (row.id)}
      <li>
        <span class="name">
          {name}
          {#if note}<small>{note}</small>{/if}
        </span>
        {@render pill(row.state, detail(row))}
      </li>
    {/each}
  </ul>
{/if}

<style>
  .summary {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .summary-text {
    display: grid;
    gap: 2px;
    min-width: 0;
  }

  .updated {
    font-size: 0.8125rem;
    color: var(--ink-soft);
  }

  .badge {
    display: inline-grid;
    flex: none;
    place-items: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
  }

  .badge[data-state='ok'],
  .pill[data-state='ok'] {
    background: var(--state-ok-bg);
    color: var(--state-ok-ink);
  }

  .badge[data-state='partial'],
  .pill[data-state='partial'] {
    background: var(--state-partial-bg);
    color: var(--state-partial-ink);
  }

  .badge[data-state='stale'],
  .pill[data-state='stale'] {
    background: var(--state-stale-bg);
    color: var(--state-stale-ink);
  }

  .badge[data-state='down'],
  .pill[data-state='down'] {
    background: var(--state-down-bg);
    color: var(--state-down-ink);
  }

  .rows {
    display: grid;
    gap: 8px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  li {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 10px;
    font-size: 0.9375rem;
    color: var(--ink);
  }

  .name {
    display: grid;
    min-width: 0;
  }

  .name small {
    font-size: 0.8125rem;
    color: var(--ink-soft);
  }

  .pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 2px 9px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    white-space: nowrap;
  }
</style>
