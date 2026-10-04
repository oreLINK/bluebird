<!--
  Back of a tile, for both KPI kinds (lib/kpiView.ts): what the KPI is, how it
  is computed (config/kpis.yaml `method`, with its params filled in), then
    live:        the time window studied, today's reliability (from the
                 confidence of every station) and the last update;
    historical:  the season (Rewind dates) and when it was computed;
  and finally the data sources and the banner photo credit.
-->
<script lang="ts">
  import ConfidenceDots from '../components/ConfidenceDots.svelte';
  import Icon from '../components/Icon.svelte';
  import type { Tile } from '../lib/config';
  import { todayIn } from '../lib/data';
  import {
    formatDate,
    formatLongDate,
    formatMethod,
    formatPercent,
    formatTime,
    formatWindow,
  } from '../lib/format';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import type { KpiView } from '../lib/kpiView';
  import type { Photo } from '../lib/photos';
  import { reliability, sharedWindow } from '../lib/ranking';

  let { tile, view, photo }: { tile: Tile; view: KpiView; photo?: Photo } = $props();

  const kpi = $derived(view.kpi);
  const ranking = $derived(view.kind === 'live' ? view.ranking : []);
  const today = $derived(reliability(ranking));
  const timeWindow = $derived(sharedWindow(ranking));
  const method = $derived(
    kpi.method ? formatMethod(i18n.pick(kpi.method), kpi.params, i18n.locale) : '',
  );
</script>

<div class="back-content">
  <header>
    <p class="eyebrow">
      {#if view.kind === 'historical'}
        <Icon name="rewind" size={14} />
        {i18n.pick(view.rewind.name)}
      {:else}
        {#if tile.icon}<Icon name={tile.icon} size={14} />{/if}
        {i18n.t('back.eyebrow')}
      {/if}
    </p>
    <h3>{i18n.pick(kpi.name)}</h3>
  </header>

  <section>
    <h4>{i18n.t('back.what')}</h4>
    <p class="strong">{i18n.pick(kpi.description)}</p>
  </section>

  {#if view.kind === 'historical'}
    <section>
      <h4>{i18n.t('back.season')}</h4>
      <p class="strong tabular">
        {i18n.t('rewind.period', {
          start: formatDate(view.rewind.start, i18n.locale),
          end: formatDate(view.rewind.end, i18n.locale),
        })}
      </p>
    </section>
  {:else if ranking.length}
    <section>
      <h4>{i18n.t('tile.window')}</h4>
      <p class="strong tabular">
        {timeWindow
          ? formatWindow(
              timeWindow.start,
              timeWindow.end,
              i18n.locale,
              view.timezone,
              view.kind === 'live' ? view.forecastDate : undefined,
            )
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
      <div class="meter">
        <ConfidenceDots level={today.level} size={10} />
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
  {/if}

  {#if view.generatedAt}
    <section>
      <h4>{i18n.t('back.updateTitle')}</h4>
      <p>
        {#if view.kind === 'historical'}
          {i18n.t('rewind.computed', { date: formatDate(view.generatedAt.slice(0, 10), i18n.locale) })}
        {:else}
          {i18n.t('back.updated', {
            date: formatLongDate(todayIn(view.timezone, new Date(view.generatedAt)), i18n.locale),
            time: formatTime(view.generatedAt, i18n.locale, view.timezone),
          })}
        {/if}
      </p>
    </section>
  {/if}

  {#if view.sources.length}
    <section>
      <h4>{i18n.t('footer.sources')}</h4>
      <ul class="sources">
        {#each view.sources as source (source.id)}
          <li>
            <a href={source.url} target="_blank" rel="noopener noreferrer">{source.name}</a>
            {#if source.license}<span>({source.license})</span>{/if}
          </li>
        {/each}
      </ul>
    </section>
  {/if}

  {#if photo?.credit}
    <section>
      <h4>{i18n.t('back.photo')}</h4>
      <p>
        {#if photo.credit.url}
          <a class="credit" href={photo.credit.url} target="_blank" rel="noopener noreferrer"
            >{photo.credit.author}</a
          >
        {:else}
          {photo.credit.author}
        {/if}
        {#if photo.credit.license}<span class="license">({photo.credit.license})</span>{/if}
      </p>
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

  .credit {
    color: var(--link);
    font-weight: 600;
  }

  .license,
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
