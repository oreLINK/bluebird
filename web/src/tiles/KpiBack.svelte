<!--
  Back of a tile: what the KPI is, how it is computed (config/kpis.yaml
  `method`, with its params filled in) and how reliable it is today, from the
  confidence of every station in the current data.
-->
<script lang="ts">
  import Icon from '../components/Icon.svelte';
  import type { Kpi, Tile } from '../lib/config';
  import type { MassifDaily } from '../lib/data';
  import {
    formatLongDate,
    formatMethod,
    formatPercent,
    formatTime,
    formatWindow,
  } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { reliability, sharedWindow } from '../lib/ranking';

  let { tile, kpi, data }: { tile: Tile; kpi: Kpi | undefined; data: MassifDaily } = $props();

  const ranking = $derived(kpi ? (data.kpis[kpi.id]?.ranking ?? []) : []);
  const today = $derived(reliability(ranking));
  const timeWindow = $derived(sharedWindow(ranking));
  const method = $derived(
    kpi?.method ? formatMethod(i18n.pick(kpi.method), kpi.params, i18n.locale) : '',
  );
</script>

<div class="back-content">
  <header>
    <p class="eyebrow">
      {#if tile.icon}<Icon name={tile.icon} size={14} />{/if}
      {i18n.t('back.eyebrow')}
    </p>
    <h3>{i18n.pick(kpi?.name)}</h3>
  </header>

  {#if kpi}
    <section>
      <h4>{i18n.t('back.what')}</h4>
      <p class="strong">{i18n.pick(kpi.description)}</p>
    </section>
  {/if}

  {#if ranking.length}
    <section>
      <h4>{i18n.t('tile.window')}</h4>
      <p class="strong tabular">
        {timeWindow
          ? formatWindow(timeWindow.start, timeWindow.end, i18n.locale, data.timezone)
          : i18n.t('back.windowVaries')}
      </p>
    </section>
  {/if}

  <section>
    <h4>{i18n.t('back.method')}</h4>
    <p>{method || i18n.t('back.noMethod')}</p>
  </section>

  {#if today}
    <section>
      <h4>{i18n.t('back.reliability')}</h4>
      <div class="meter" data-level={today.level}>
        <span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>
        <strong>{i18n.t(`confidence.${today.level}`)}</strong>
        <span class="index tabular">
          {i18n.t('back.index', { score: formatPercent(today.score, i18n.locale) })}
        </span>
      </div>
      <p class="help">{i18n.t('back.reliabilityHelp')}</p>
      <ul>
        <li>{i18n.t('back.breakdown', today.counts)}</li>
        <li>{i18n.t('back.scenarios', { members: today.members })}</li>
      </ul>
    </section>

    <section>
      <h4>{i18n.t('back.updateTitle')}</h4>
      <p>
        {i18n.t('back.updated', {
          date: formatLongDate(data.forecast_date, i18n.locale),
          time: formatTime(data.generated_at, i18n.locale, data.timezone),
        })}
      </p>
    </section>
  {/if}

  {#if data.sources.length}
    <section>
      <h4>{i18n.t('footer.sources')}</h4>
      <ul class="sources">
        {#each data.sources as source (source.id)}
          <li>
            <a href={source.url} target="_blank" rel="noopener noreferrer">{source.name}</a>
            {#if source.license}<span>({source.license})</span>{/if}
          </li>
        {/each}
      </ul>
    </section>
  {/if}
</div>

<style>
  .back-content {
    display: grid;
    gap: 12px;
    padding: 16px 56px 18px 18px;
    font-size: 0.875rem;
    line-height: 1.45;
    color: var(--ink-soft);
  }

  .eyebrow {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.6875rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--prob-high);
  }

  header {
    display: grid;
    gap: 4px;
  }

  .strong {
    color: var(--ink);
  }

  .sources {
    list-style: none;
    padding: 0;
    font-size: 0.8125rem;
  }

  .sources a {
    color: var(--link);
    font-weight: 600;
  }

  .sources span {
    color: var(--ink-faint);
  }

  h3 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 1.625rem;
    font-style: italic;
    font-weight: 800;
    line-height: 1.1;
    color: var(--ink);
  }

  section {
    display: grid;
    gap: 6px;
    padding-top: 10px;
    border-top: 1px solid var(--line);
  }

  h4 {
    margin: 0;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }

  .meter {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--ink);
  }

  .meter strong {
    font-family: var(--font-display);
    font-size: 1.375rem;
    font-style: italic;
    font-weight: 800;
    text-transform: capitalize;
  }

  .index {
    margin-left: auto;
    padding: 2px 10px;
    border-radius: 999px;
    background: var(--pill-bg);
    color: var(--pill-ink);
    font-weight: 700;
  }

  .dots {
    display: inline-flex;
    gap: 4px;
  }

  .dots i {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--track);
  }

  [data-level='low'] .dots i:nth-child(-n + 1),
  [data-level='medium'] .dots i:nth-child(-n + 2),
  [data-level='high'] .dots i {
    background: var(--prob-high);
  }

  .help {
    font-size: 0.8125rem;
    color: var(--ink-faint);
  }

  ul {
    display: grid;
    gap: 4px;
    margin: 0;
    padding-left: 18px;
  }

</style>
