<!--
  Back of a tile, for both KPI kinds (lib/kpiView.ts): what the KPI is, how it
  is computed (config/kpis.yaml `method`, with its params filled in), then
    live:        when (the time badge, the period in words and its exact date:
                 "Demain matin · Samedi 16 janvier, de 06:00 à 12:00"), the
                 time window studied, today's reliability (from the
                 confidence of every station) and the last update;
    historical:  the season (Rewind dates) and when it was computed;
  and finally the data sources and the banner photo credit.
  A `certified` KPI (an official value relayed as is, e.g. the avalanche
  bulletin) adds a "Donnée officielle" box under the description, explaining
  the rosette of the front, and a reliability text based on the bulletin's
  freshness (no scenarios). A `scale` display lists every level with its
  name and advice ("Que faire selon le niveau ?").
-->
<script lang="ts">
  import CertifiedBadge from '../components/CertifiedBadge.svelte';
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
  import { displayOf, type KpiView } from '../lib/kpiView';
  import { slotDates, type TileTime } from '../lib/periods';
  import type { Photo } from '../lib/photos';
  import TimeBadge from './TimeBadge.svelte';
  import { reliability, sharedWindow } from '../lib/ranking';

  let {
    tile,
    view,
    photo,
    time = null,
  }: { tile: Tile; view: KpiView; photo?: Photo; time?: TileTime | null } = $props();

  const capitalize = (text: string) => text.charAt(0).toLocaleUpperCase(i18n.locale) + text.slice(1);
  /** The exact date of the period shown, in words. */
  const when = $derived.by(() => {
    if (view.kind !== 'live' || !view.slot) return '';
    const dates = slotDates(view.slot, view.timezone);
    const date = formatLongDate(dates.date, i18n.locale);
    if (dates.kind === 'day') return capitalize(i18n.t('back.whenDay', { date }));
    if (dates.kind === 'night') {
      return capitalize(i18n.t('back.whenNight', { date, next: formatLongDate(dates.next, i18n.locale) }));
    }
    if (dates.kind === 'date') return capitalize(i18n.t('back.whenDate', { date }));
    return capitalize(
      i18n.t('back.whenSlot', {
        date,
        start: formatTime(dates.start, i18n.locale, view.timezone),
        end: formatTime(dates.end, i18n.locale, view.timezone),
      }),
    );
  });

  const kpi = $derived(view.kpi);
  const ranking = $derived(view.kind === 'live' ? view.ranking : []);
  const today = $derived(reliability(ranking));
  const timeWindow = $derived(sharedWindow(ranking));
  const certified = $derived(Boolean(kpi.certified));
  const steps = $derived(view.kind === 'live' && displayOf(kpi).kind === 'scale' ? (kpi.display?.steps ?? []) : []);
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

  {#if certified}
    <section class="certified">
      <h4>{i18n.t('back.certified')}</h4>
      <div class="certified-box">
        <CertifiedBadge size={28} />
        <div>
          <strong>{i18n.t('back.certifiedTitle')}</strong>
          <p>{i18n.t('back.certifiedText')}</p>
          {#if kpi.official_link}
            <a class="official" href={kpi.official_link.url} target="_blank" rel="noopener noreferrer">
              {i18n.pick(kpi.official_link.label)}
              <Icon name="external" size={15} />
              <span class="visually-hidden">{i18n.t('back.newTab')}</span>
            </a>
          {/if}
        </div>
      </div>
    </section>
  {/if}

  {#if steps.length}
    <section>
      <h4>{i18n.t('back.scale')}</h4>
      <ol class="steps">
        {#each steps as step (step.value)}
          <li>
            <span class="step-value tabular" data-scale={step.tone}><span>{step.value}</span></span>
            <div>
              <strong>{i18n.pick(step.label)}</strong>
              {#if step.advice}<p>{i18n.pick(step.advice)}</p>{/if}
            </div>
          </li>
        {/each}
      </ol>
    </section>
  {/if}

  {#if time && when}
    <section>
      <h4>{i18n.t('back.when')}</h4>
      <p class="when">
        <TimeBadge {time} />
        <strong>{capitalize(i18n.pick(time.label))}</strong>
      </p>
      <p class="strong">{when}</p>
      <p class="help">{i18n.t('back.whenHelp')}</p>
    </section>
  {/if}

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
      <p class="help">
        {i18n.t(certified ? 'back.reliabilityHelpOfficial' : 'back.reliabilityHelp')}
      </p>
      <ul>
        <li>{i18n.t('back.breakdown', today.counts)}</li>
        {#if today.members > 0}
          <li>{i18n.t('back.scenarios', { members: today.members })}</li>
        {/if}
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

  .when {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
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
    letter-spacing: var(--display-tracking);
    font-size: 1.625rem;
    font-weight: var(--display-weight);
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
    letter-spacing: var(--display-tracking);
    font-size: 1.375rem;
    font-weight: var(--display-weight);
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

  .certified-box {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 12px;
    border-radius: var(--radius-m);
    background: color-mix(in srgb, var(--verified-bg) 10%, transparent);
    border: 1px solid color-mix(in srgb, var(--verified-bg) 35%, transparent);
  }

  .certified-box strong {
    color: var(--ink);
  }

  .certified-box p {
    margin-bottom: 8px;
  }

  /* The way to the source itself: a real link, opened in a new tab. */
  .official {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-height: 2.25rem;
    padding: 6px 14px;
    border-radius: 999px;
    /* Brand pair: >= 4.5:1 in both modes (white on --verified-bg is not in dark). */
    background: var(--brand);
    color: var(--on-brand);
    font-weight: 700;
    text-decoration: none;
  }

  .official:focus-visible {
    outline: 3px solid var(--focus);
    outline-offset: 2px;
  }

  .steps {
    display: grid;
    gap: 8px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .steps li {
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }

  .steps strong {
    color: var(--ink);
  }

  /* The level on its official colour, as on the odds buttons (base.css [data-scale]). */
  .step-value {
    flex: none;
    display: grid;
    place-items: center;
    width: 2rem;
    height: 2rem;
    border-radius: 8px;
    border: 1px solid var(--scale-edge, color-mix(in srgb, var(--scale-bg) 70%, #000000));
    background: var(--scale-fill, var(--scale-bg));
    color: var(--scale-ink);
    font-family: var(--font-display);
    font-size: 1.0625rem;
    font-weight: var(--display-weight);
    text-shadow: var(--scale-number-shadow, none);
  }

</style>
