<!--
  Footer "Service status": the health of the last refresh (diamond/status.json).
  A summary line (all fine, or how many items are degraded, with the refresh
  time) opens a list of every data source, transformation, indicator and tile
  of the current massif, each with its state. States carry an icon and a word,
  never colour alone. Periods already over are not listed.
-->
<script lang="ts">
  import { kpis, sources, tiles } from '../lib/config';
  import type { ServiceStatus } from '../lib/data';
  import { formatLongDate, formatTime } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { instanceTitle } from '../lib/periods';
  import { STATE_ICON, type StateId, type StatusRow, periodLabel, statusView } from '../lib/status';
  import Icon from './Icon.svelte';

  let {
    status,
    massifId,
    timezone,
    now,
  }: { status: ServiceStatus | null; massifId: string; timezone: string; now: number } = $props();

  const view = $derived(status ? statusView(status, massifId, now) : null);

  const sourceName = (id: string) =>
    sources.find((s) => s.id === id)?.attribution.name ?? id;
  const kpiName = (id: string) => i18n.pick(kpis.find((k) => k.id === id)?.name) || id;

  function periodText(period: Parameters<typeof periodLabel>[1]): string {
    if (!status) return period.key;
    return i18n.pick(periodLabel(status, period, timezone, now)) || period.key;
  }

  function tileName(tileId: string, period: Parameters<typeof periodLabel>[1]): string {
    const tile = tiles.find((t) => t.id === tileId);
    if (!tile || !status) return tileId;
    const label = periodLabel(status, period, timezone, now) ?? { fr: '', en: '' };
    const tileKpis = kpis.filter((k) => tile.kpis?.includes(k.id));
    return i18n.pick(instanceTitle(tile, tileKpis, label)).trim();
  }

  function detail(row: StatusRow): string {
    const parts: string[] = [];
    if (row.state === 'stale' && row.since) {
      parts.push(i18n.t('service.since', { time: formatTime(row.since, i18n.locale, timezone) }));
    } else if (row.state === 'partial' && row.expected) {
      parts.push(i18n.t('service.stations', { ok: row.ok ?? 0, expected: row.expected }));
    }
    return parts.join(' · ');
  }
</script>

{#snippet pill(state: StateId, extra: string)}
  <span class="pill" data-state={state}>
    <Icon name={STATE_ICON[state]} size={14} />
    <span>{i18n.t(`state.${state}`)}{extra ? ` · ${extra}` : ''}</span>
  </span>
{/snippet}

{#snippet group(title: string, rows: { name: string; row: StatusRow; note?: string }[])}
  {#if rows.length}
    <section>
      <h3>{title}</h3>
      <ul>
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
    </section>
  {/if}
{/snippet}

<div class="service" data-state={view?.state ?? 'down'}>
  {#if status && view}
    <details>
      <summary>
        <span class="badge" data-state={view.state}><Icon name={STATE_ICON[view.state]} size={16} /></span>
        <span class="summary-text">
          <strong>{i18n.t('service.title')}</strong>
          <span>
            {view.degraded === 0
              ? i18n.t('service.allOk')
              : i18n.t('service.degraded', { count: view.degraded })}
          </span>
          <span class="updated">
            {i18n.t('service.updated', {
              date: formatLongDate(
                new Intl.DateTimeFormat('en-CA', { timeZone: timezone }).format(
                  new Date(status.generated_at),
                ),
                i18n.locale,
              ),
              time: formatTime(status.generated_at, i18n.locale, timezone),
            })}
          </span>
        </span>
        <span class="chevron"><Icon name="chevron" size={18} /></span>
      </summary>

      <div class="groups">
        {@render group(
          i18n.t('service.sources'),
          view.sources.map((row) => ({ name: sourceName(row.id), row })),
        )}
        {@render group(
          i18n.t('service.transforms'),
          view.transforms.map((row) => ({
            name: i18n.t('service.transformOf', { source: sourceName(row.id) }),
            row,
          })),
        )}
        {@render group(
          i18n.t('service.kpis'),
          view.kpis.map((row) => ({
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
          })),
        )}
        {@render group(
          i18n.t('service.tiles'),
          view.tiles.map((row) => ({ name: tileName(row.tileId, row.period), row })),
        )}
      </div>
    </details>
  {:else}
    <p class="unavailable">
      <span class="badge" data-state="down"><Icon name="alert" size={16} /></span>
      {i18n.t('service.unavailable')}
    </p>
  {/if}
</div>

<style>
  .service {
    border-top: 1px solid var(--line);
    padding-top: 10px;
  }

  summary {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 2.75rem;
    cursor: pointer;
    list-style: none;
  }

  summary::-webkit-details-marker {
    display: none;
  }

  summary:focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 2px;
    border-radius: var(--radius-s);
  }

  .summary-text {
    display: grid;
    gap: 1px;
    min-width: 0;
    color: var(--ink-soft);
  }

  .summary-text strong {
    color: var(--ink);
  }

  .updated {
    font-size: 0.75rem;
    color: var(--ink-faint);
  }

  .chevron {
    margin-left: auto;
    color: var(--ink-faint);
    transition: transform 0.2s ease;
  }

  details[open] .chevron {
    transform: rotate(180deg);
  }

  @media (prefers-reduced-motion: reduce) {
    .chevron {
      transition: none;
    }
  }

  .badge {
    display: inline-grid;
    flex: none;
    place-items: center;
    width: 28px;
    height: 28px;
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

  .groups {
    display: grid;
    gap: 14px;
    padding-top: 12px;
  }

  h3 {
    margin: 0 0 6px;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }

  ul {
    display: grid;
    gap: 6px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  li {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 10px;
  }

  .name {
    display: grid;
    min-width: 0;
    color: var(--ink);
  }

  .name small {
    font-size: 0.75rem;
    color: var(--ink-faint);
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

  .unavailable {
    display: flex;
    align-items: center;
    gap: 10px;
  }
</style>
