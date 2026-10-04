<!--
  "Data from 06:00": shown on a tile whose values come from an earlier refresh
  than the page (the KPI could not be recomputed since). Positioned by its
  parent; the text keeps ≥ 4.5:1 contrast on its own background.
-->
<script lang="ts">
  import { formatTime } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import Icon from './Icon.svelte';

  let { since, timezone, class: className = '' }: { since: string; timezone: string; class?: string } =
    $props();
</script>

<p class="stale-badge {className}">
  <Icon name="clock" size={14} />
  <span>{i18n.t('tile.staleSince', { time: formatTime(since, i18n.locale, timezone) })}</span>
</p>

<style>
  .stale-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    width: max-content;
    padding: 3px 9px;
    border-radius: 999px;
    background: var(--state-stale-bg);
    color: var(--state-stale-ink);
    font-size: 0.75rem;
    font-weight: 700;
    line-height: 1.3;
  }
</style>
