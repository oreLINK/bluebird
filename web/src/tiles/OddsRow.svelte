<!--
  The best stations of a KPI as betting-style "odds buttons": name and
  percentage, a probability bar below each. `overlay` adapts the bars for a
  photo or illustration background (TileBannerFull).
-->
<script lang="ts">
  import type { RankingEntry, StationInfo } from '../lib/data';
  import { formatOdds, formatPercent } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';

  let {
    tileId,
    label,
    top,
    selected,
    onselect,
    stations,
    showOdds = false,
    overlay = false,
  }: {
    tileId: string;
    label: string;
    top: RankingEntry[];
    selected: string | null;
    onselect: (stationId: string) => void;
    stations: Record<string, StationInfo>;
    showOdds?: boolean;
    overlay?: boolean;
  } = $props();

  const shortName = (id: string) => stations[id]?.short_name ?? stations[id]?.name ?? id;
  const fullName = (id: string) => stations[id]?.name ?? id;
</script>

<div class="odds" class:overlay role="group" aria-label={label} style="--n: {top.length}">
  {#each top as entry, index (entry.station_id)}
    <div class="odd">
      <button
        type="button"
        class="odd-button"
        aria-pressed={selected === entry.station_id}
        aria-controls="{tileId}-top-details"
        aria-label={i18n.t('a11y.rowSummary', {
          rank: index + 1,
          station: fullName(entry.station_id),
          percent: formatPercent(entry.probability, i18n.locale),
        })}
        onclick={() => onselect(entry.station_id)}
      >
        <span class="odd-name" aria-hidden="true">{shortName(entry.station_id)}</span>
        <span class="odd-value tabular" aria-hidden="true">
          {formatPercent(entry.probability, i18n.locale)}
        </span>
        {#if showOdds}
          <span class="odd-odds tabular" aria-hidden="true">
            {i18n.t('tile.odds', { odds: formatOdds(entry.probability, i18n.locale) })}
          </span>
        {/if}
      </button>
      <span class="odd-bar" aria-hidden="true"><span style="--p: {entry.probability}"></span></span>
    </div>
  {/each}
</div>

<style>
  .odds {
    display: grid;
    grid-template-columns: repeat(var(--n, 3), minmax(0, 1fr));
    gap: 8px;
    padding-top: 6px;
  }

  .odd {
    display: grid;
    gap: 7px;
    min-width: 0;
  }

  .odd-button {
    position: relative;
    display: grid;
    /* Fixed size: two lines of name (2 × 0.75rem × 1.2) and the percentage. */
    grid-template-rows: 1.8rem auto;
    justify-items: center;
    align-items: center;
    gap: 2px;
    height: 4.75rem;
    padding: 10px 6px 8px;
    border-radius: var(--radius-m);
    border: 1px solid var(--pill-border);
    background: var(--pill-bg);
    color: var(--pill-ink);
    text-align: center;
    cursor: pointer;
    transition:
      background 0.15s ease,
      color 0.15s ease;
  }

  .odd-button[aria-pressed='true'] {
    background: var(--pill-active-bg);
    border-color: var(--pill-active-bg);
    color: var(--pill-active-ink);
  }

  .overlay .odd-button {
    box-shadow: 0 6px 16px -8px rgba(0, 0, 0, 0.6);
  }

  .odd-name {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    overflow: hidden;
    font-size: 0.75rem;
    font-weight: 600;
    line-height: 1.2;
    overflow-wrap: anywhere;
  }

  .odd-value {
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-style: italic;
    font-weight: 800;
    line-height: 1.05;
  }

  .odd-odds {
    font-size: 0.6875rem;
    font-weight: 600;
    opacity: 0.85;
  }

  .odd-bar {
    display: block;
    height: 4px;
    margin: 0 8px;
    border-radius: 999px;
    background: var(--track);
    overflow: hidden;
  }

  .overlay .odd-bar {
    background: rgba(255, 255, 255, 0.28);
  }

  .odd-bar > span {
    display: block;
    height: 100%;
    width: calc(var(--p) * 100%);
    border-radius: inherit;
    background: color-mix(in oklch, var(--prob-high) calc(var(--p) * 100%), var(--prob-low));
  }

  .overlay .odd-bar > span {
    background: var(--sky);
  }
</style>
