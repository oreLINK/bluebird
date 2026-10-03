<!--
  One ranked station: rank, name, probability bar and pill. Tapping it toggles
  its StationDetails. Shared by every tile type.
-->
<script lang="ts">
  import Icon from '../components/Icon.svelte';
  import ProbabilityPill from '../components/ProbabilityPill.svelte';
  import type { Kpi } from '../lib/config';
  import type { RankingEntry, StationInfo } from '../lib/data';
  import { formatPercent } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import StationDetails from './StationDetails.svelte';

  let {
    id,
    rank,
    entry,
    kpi,
    station,
    timezone,
    open,
    ontoggle,
    showOdds = false,
    showWindow = false,
  }: {
    id: string;
    rank: number;
    entry: RankingEntry;
    kpi: Kpi | undefined;
    station: StationInfo | undefined;
    timezone: string;
    open: boolean;
    ontoggle: () => void;
    showOdds?: boolean;
    showWindow?: boolean;
  } = $props();

  const name = $derived(station?.short_name ?? station?.name ?? entry.station_id);
  const fullName = $derived(station?.name ?? entry.station_id);
</script>

<li class:open>
  <button
    type="button"
    class="row"
    aria-expanded={open}
    aria-controls="{id}-details"
    aria-label={i18n.t('a11y.rowSummary', {
      rank,
      station: fullName,
      percent: formatPercent(entry.probability, i18n.locale),
    })}
    onclick={ontoggle}
  >
    <span class="rank tabular" aria-hidden="true">{rank}</span>
    <span class="who" aria-hidden="true">
      <span class="name">
        {name}
      </span>
      <span class="bar"><span style="--p: {entry.probability}"></span></span>
    </span>
    <span aria-hidden="true"><ProbabilityPill probability={entry.probability} {showOdds} /></span>
    <Icon name="chevron" size={18} class="chevron" />
  </button>
  {#if open}
    <div class="details-wrap">
      <StationDetails id="{id}-details" {entry} {kpi} {station} {timezone} {showWindow} />
    </div>
  {/if}
</li>

<style>
  li {
    list-style: none;
    border-bottom: 1px solid var(--line);
  }

  li:last-child {
    border-bottom: 0;
  }

  .row {
    display: grid;
    grid-template-columns: 1.5rem minmax(0, 1fr) auto 18px;
    align-items: center;
    gap: 10px;
    width: 100%;
    min-height: 3.5rem;
    padding: 8px 4px;
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
  }

  .row :global(.chevron) {
    color: var(--ink-faint);
    transition: transform 0.2s ease;
  }

  li.open .row :global(.chevron) {
    transform: rotate(180deg);
  }

  .details-wrap {
    padding: 0 0 12px 34px;
  }
</style>
