<!--
  Plain text above the tiles (no card). The massif is not repeated: it is
  selected in the massif bar of the header.
    - Live data: the reference date of the data (the day of their last update
      in the massif timezone), and a small line with the update time. When the
      last update is older than expected (refreshes run every 6 hours), a
      notice says the next one is not available yet.
    - A Rewind filter (`rewind` set): "Saison 2025/2026" (years of its start
      and end dates), and a small line saying it is a season review.
-->
<script lang="ts">
  import type { Rewind } from '../lib/config';
  import { type MassifDaily, todayIn } from '../lib/data';
  import { formatLongDate, formatSeason, formatTime } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';

  let {
    data = null,
    rewind,
    now = Date.now(),
  }: { data?: MassifDaily | null; rewind?: Rewind; now?: number } = $props();

  /** A refresh every 6 hours, plus margin for late GitHub Actions runs. */
  const STALE_AFTER_MS = 7 * 3600_000;

  const lines = $derived.by(() => {
    if (rewind) {
      return {
        title: i18n.t('rewind.season', { years: formatSeason(rewind.start, rewind.end) }),
        detail: i18n.t('rewind.statusDetail'),
      };
    }
    if (!data) return null;
    const day = formatLongDate(todayIn(data.timezone, new Date(data.generated_at)), i18n.locale);
    return {
      title: day,
      detail: i18n.t('status.updatedAt', {
        time: formatTime(data.generated_at, i18n.locale, data.timezone),
      }),
      late:
        now - Date.parse(data.generated_at) > STALE_AFTER_MS
          ? i18n.t('status.stale', { date: day })
          : '',
    };
  });
</script>

{#if lines}
  <div class="status" class:rewind>
    <p class="date">{lines.title}</p>
    <p class="updated tabular">{lines.detail}</p>
    {#if 'late' in lines && lines.late}<p class="updated">{lines.late}</p>{/if}
  </div>
{/if}

<style>
  .status {
    display: grid;
    gap: 2px;
    padding: 16px 2px 14px;
  }

  .date {
    font-family: var(--font-display);
    font-size: 1.625rem;
    font-weight: 800;
    font-style: italic;
    line-height: 1.1;
    color: var(--ink);
  }

  .date::first-letter {
    text-transform: uppercase;
  }

  .rewind .date {
    color: var(--rewind-ink);
  }

  .updated {
    font-size: 0.8125rem;
    color: var(--ink-faint);
  }
</style>
