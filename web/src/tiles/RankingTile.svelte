<!--
  Tile type `ranking`: stations sorted by probability, betting-site style.
  Reads the first KPI of the tile. Options (config/tiles.yaml):
    visible_rows: rows shown before "see all" (default 5)
    show_odds:    also show decimal odds 1/p (default false)
  Tapping a row reveals the explanatory drivers declared in config/kpis.yaml.
-->
<script lang="ts">
  import ProbabilityPill from '../components/ProbabilityPill.svelte';
  import Icon from '../components/Icon.svelte';
  import { formatDriver, formatPercent, formatWindow } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import type { TileProps } from './registry';
  import TileShell from './TileShell.svelte';
  import { booleanOption, numberOption } from './options';

  let { tile, kpis, data }: TileProps = $props();

  const kpi = $derived(kpis[0]);
  const ranking = $derived(kpi ? (data.kpis[kpi.id]?.ranking ?? []) : []);
  const visibleRows = $derived(numberOption(tile.options, 'visible_rows', 5));
  const showOdds = $derived(booleanOption(tile.options, 'show_odds', false));

  let showAll = $state(false);
  let openStation = $state<string | null>(null);

  const rows = $derived(showAll ? ranking : ranking.slice(0, visibleRows));
  const title = $derived(i18n.pick(tile.title ?? kpi?.name));
  const subtitle = $derived(kpi ? i18n.pick(kpi.description) : '');

  /** Shared time window, when every station has the same one. */
  const sharedWindow = $derived.by(() => {
    const first = ranking[0];
    if (!first) return null;
    const same = ranking.every(
      (r) => r.window_start === first.window_start && r.window_end === first.window_end,
    );
    return same ? formatWindow(first.window_start, first.window_end, i18n.locale, data.timezone) : null;
  });

  function toggle(stationId: string) {
    openStation = openStation === stationId ? null : stationId;
  }

  function driverRows(drivers: Record<string, number | string | null>) {
    return Object.entries(kpi?.drivers ?? {}).flatMap(([key, spec]) => {
      const value = formatDriver(drivers[key], i18n.locale, spec.unit, spec.decimals ?? 0);
      return value === null ? [] : [{ key, label: i18n.pick(spec.label), value }];
    });
  }
</script>

<TileShell id={tile.id} {title} {subtitle} icon={tile.icon}>
  {#if ranking.length === 0}
    <p class="empty">{i18n.t('tile.noRanking')}</p>
  {:else}
    {#if sharedWindow}
      <p class="window tabular">{i18n.t('tile.window')} · {sharedWindow}</p>
    {/if}
    <ol class="ranking">
      {#each rows as entry, index (entry.station_id)}
        {@const station = data.stations[entry.station_id]}
        {@const open = openStation === entry.station_id}
        {@const detailsId = `${tile.id}-${entry.station_id}-details`}
        <li class:open>
          <button
            type="button"
            class="row"
            aria-expanded={open}
            aria-controls={detailsId}
            aria-label={i18n.t('a11y.rowSummary', {
              rank: index + 1,
              station: station?.name ?? entry.station_id,
              percent: formatPercent(entry.probability, i18n.locale),
            })}
            onclick={() => toggle(entry.station_id)}
          >
            <span class="rank tabular" aria-hidden="true">{index + 1}</span>
            <span class="who" aria-hidden="true">
              <span class="name">
                {station?.name ?? entry.station_id}
                {#if index === 0 && entry.probability >= 0.5}
                  <span class="badge">{i18n.t('tile.favourite')}</span>
                {/if}
              </span>
              <span class="bar"><span style="--p: {entry.probability}"></span></span>
            </span>
            <span aria-hidden="true"><ProbabilityPill probability={entry.probability} {showOdds} /></span>
            <Icon name="chevron" size={18} class="chevron" />
          </button>
          {#if open}
            <dl class="details" id={detailsId}>
              {#if !sharedWindow}
                <div>
                  <dt>{i18n.t('tile.window')}</dt>
                  <dd class="tabular">
                    {formatWindow(entry.window_start, entry.window_end, i18n.locale, data.timezone)}
                  </dd>
                </div>
              {/if}
              {#each driverRows(entry.drivers) as driver (driver.key)}
                <div>
                  <dt>{driver.label}</dt>
                  <dd class="tabular">{driver.value}</dd>
                </div>
              {/each}
              <div>
                <dt>{i18n.t('tile.confidence')}</dt>
                <dd>
                  <span class="confidence" data-level={entry.confidence} aria-hidden="true">
                    <i></i><i></i><i></i>
                  </span>
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
          {/if}
        </li>
      {/each}
    </ol>
  {/if}

  {#snippet footer()}
    {#if ranking.length > visibleRows}
      <button type="button" class="more" onclick={() => (showAll = !showAll)}>
        {showAll ? i18n.t('tile.seeLess') : i18n.t('tile.seeAll', { count: ranking.length })}
      </button>
    {/if}
  {/snippet}
</TileShell>

<style>
  .empty,
  .window {
    padding: 0 4px 10px;
    font-size: 0.8125rem;
    color: var(--ink-faint);
  }

  .ranking {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 6px;
  }

  li {
    border-radius: var(--radius-m);
    background: color-mix(in srgb, var(--glass-bg-strong) 70%, transparent);
    border: 1px solid var(--hairline);
    overflow: hidden;
  }

  .row {
    display: grid;
    grid-template-columns: 1.5rem minmax(0, 1fr) auto 18px;
    align-items: center;
    gap: 10px;
    width: 100%;
    min-height: 3.5rem;
    padding: 8px 10px 8px 12px;
    border: 0;
    background: transparent;
    text-align: left;
    cursor: pointer;
  }

  .rank {
    font-size: 0.9375rem;
    font-weight: 700;
    color: var(--ink-faint);
    text-align: center;
  }

  .who {
    display: grid;
    gap: 6px;
    min-width: 0;
  }

  .name {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    overflow: hidden;
    font-weight: 600;
    font-size: 0.9375rem;
    line-height: 1.25;
    overflow-wrap: anywhere;
  }

  .badge {
    display: inline-block;
    margin-left: 4px;
    vertical-align: 1px;
    padding: 1px 7px;
    border-radius: 999px;
    font-size: 0.6875rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    color: var(--accent-ink);
    background: var(--accent);
  }

  .bar {
    display: block;
    height: 4px;
    border-radius: 999px;
    background: var(--track);
    overflow: hidden;
  }

  .bar > span {
    display: block;
    height: 100%;
    width: calc(var(--p) * 100%);
    border-radius: inherit;
    background: color-mix(in oklch, var(--prob-high) calc(var(--p) * 100%), var(--prob-low));
    transition: width 0.4s ease;
  }

  .row :global(.chevron) {
    color: var(--ink-faint);
    transition: transform 0.2s ease;
  }

  li.open .row :global(.chevron) {
    transform: rotate(180deg);
  }

  .details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(7.5rem, 1fr));
    gap: 10px 14px;
    margin: 0;
    padding: 4px 14px 14px 46px;
    font-size: 0.8125rem;
  }

  .details dt {
    color: var(--ink-faint);
  }

  .details dd {
    margin: 2px 0 0;
    font-weight: 600;
  }

  .confidence {
    display: inline-flex;
    gap: 3px;
    margin-right: 6px;
    vertical-align: middle;
  }

  .confidence i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--track);
  }

  .confidence[data-level='low'] i:nth-child(-n + 1),
  .confidence[data-level='medium'] i:nth-child(-n + 2),
  .confidence[data-level='high'] i {
    background: var(--accent);
  }

  .more {
    width: 100%;
    min-height: 2.75rem;
    border-radius: var(--radius-m);
    border: 1px solid var(--glass-border);
    background: var(--glass-bg-strong);
    color: var(--accent);
    font-weight: 650;
    cursor: pointer;
  }
</style>
