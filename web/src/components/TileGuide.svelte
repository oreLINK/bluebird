<!--
  Examples of the page "Lire une tuile" (config/pages.yaml, page `guide`):
    front   an example tile front (banner format) with numbered marks;
    back    an example tile back, one numbered mark per section;
    badges  every time badge: the days alone, then each moment of today
            with its hours (lib/periods.ts `timeLegend`, from periods.yaml).
  The marks are explained by the numbered paragraphs of the next section of
  the page. Static: nothing here is interactive, the drawings are images for
  screen readers (one label), the badge list is a real list.
-->
<script lang="ts">
  import { kpis, massifs, tiles } from '../lib/config';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import type { MessageKey } from '../lib/i18n/core';
  import { tileTitle, timeLegend } from '../lib/periods';
  import TimeBadge from '../tiles/TimeBadge.svelte';
  import BannerArt from './BannerArt.svelte';
  import ConfidenceDots from './ConfidenceDots.svelte';
  import Icon from './Icon.svelte';

  let { part }: { part: 'front' | 'back' | 'badges' } = $props();

  const legend = timeLegend();
  /** The example: the snow tile, this morning. */
  const exampleTime = legend.moments[0]?.time ?? legend.days[0]?.time;
  const exampleTile = tiles.find((t) => t.id === 'snowfall_today') ?? tiles[0];
  const exampleKpis = kpis.filter((k) => exampleTile?.kpis?.includes(k.id));
  const title = $derived(exampleTile ? i18n.pick(tileTitle(exampleTile, exampleKpis)) : '');
  const kpi = exampleKpis[0];
  const ODDS: [string, string, 'high' | 'medium' | 'low', number][] = [
    ['Cauterets', '18', 'high', 1],
    ['Gourette', '14', 'medium', 0.78],
    ['Peyragudes', '9', 'medium', 0.5],
  ];
  const BACK_SECTIONS: MessageKey[] = [
    'back.what',
    'back.when',
    'tile.window',
    'back.method',
    'back.reliability',
    'back.updateTitle',
    'footer.sources',
    'back.photo',
  ];
</script>

{#if part === 'front'}
  <figure class="example" role="img" aria-label={i18n.t('guide.frontAlt')}>
    <div class="card front">
      <div class="banner">
        <BannerArt scene="snowfall" skyline={massifs[0]?.skyline ?? []} />
        <div class="corner">
          {#if exampleTime}<span class="mark">
              <TimeBadge time={exampleTime} onImage /><i class="pin">1</i>
            </span>{/if}
          <span class="mark">
            <span class="live"><span class="dot"></span><Icon name="webcam" size={13} />{i18n.t('webcam.live')}</span>
            <i class="pin">2</i>
          </span>
        </div>
        <span class="mark help-mark"><span class="help">?</span><i class="pin left">3</i></span>
      </div>
      <div class="content">
        <span class="mark center"><h4>{title}</h4><i class="pin">4</i></span>
        <div class="odds">
          {#each ODDS as [name, value, level, share], index (name)}
            <div class="cell">
              <span class="mark block">
                <span class="odd">
                  <span class="name">{name}</span>
                  <span class="value">{value}<small>cm</small></span>
                  <span class="mark"><ConfidenceDots {level} />{#if index === 0}<i class="pin small">6</i>{/if}</span>
                </span>
                {#if index === 0}<i class="pin">5</i>{/if}
              </span>
              <span class="mark block">
                <span class="bar"><i style="width: {share * 100}%"></i></span>
                {#if index === 0}<i class="pin low">7</i>{/if}
              </span>
            </div>
          {/each}
        </div>
      </div>
      <div class="more">
        <span class="mark">
          <span class="see-all">{i18n.t('tile.seeAll', { count: 18 })} <Icon name="chevron" size={15} /></span>
          <i class="pin">8</i>
        </span>
      </div>
    </div>
  </figure>
{:else if part === 'back'}
  <figure class="example" role="img" aria-label={i18n.t('guide.backAlt')}>
    <div class="card back">
      <span class="mark close-mark"><span class="help solid">×</span><i class="pin left">9</i></span>
      <p class="eyebrow">{i18n.t('back.eyebrow')}</p>
      <h4 class="back-title">{kpi ? i18n.pick(kpi.name) : title}</h4>
      {#each BACK_SECTIONS as key, index (key)}
        <div class="back-section">
          <span class="mark"><h5>{i18n.t(key)}</h5><i class="pin">{index + 1}</i></span>
          {#if key === 'back.when' && exampleTime}
            <span class="row"><TimeBadge time={exampleTime} /><span class="line short"></span></span>
          {:else if key === 'back.reliability'}
            <span class="row"><ConfidenceDots level="high" size={9} /><strong>{i18n.t('confidence.high')}</strong></span>
          {:else}
            <span class="line"></span>
          {/if}
        </div>
      {/each}
    </div>
  </figure>
{:else}
  <div class="legend">
    <ul>
      {#each legend.days as item (item.time.when)}
        <li><TimeBadge time={item.time} /><span>{i18n.pick(item.name)}</span></li>
      {/each}
    </ul>
    <ul>
      {#each legend.moments as item (item.time.tone)}
        <li>
          <TimeBadge time={item.time} />
          <span>{i18n.pick(item.name)}</span>
          {#if item.hours}<span class="hours">{item.hours[0]} – {item.hours[1]}</span>{/if}
        </li>
      {/each}
    </ul>
  </div>
{/if}

<style>
  .example {
    margin: 4px 0;
  }

  .card {
    position: relative;
    max-width: 358px;
    border-radius: var(--radius-l);
    border: 1px solid var(--glass-edge);
    background: var(--card-bg, var(--surface));
    box-shadow: var(--shadow);
    overflow: visible;
  }

  /* The marks 1–3 stay inside the image, so it can clip its corners. */
  .banner {
    position: relative;
    height: 9rem;
    overflow: hidden;
    border-radius: var(--radius-l) var(--radius-l) 0 0;
  }

  .corner {
    position: absolute;
    top: 14px;
    left: 12px;
    display: grid;
    justify-items: start;
    gap: 8px;
  }

  .live {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    height: 1.625rem;
    padding: 0 10px 0 8px;
    border-radius: 999px;
    background: var(--live-bg);
    color: var(--on-live);
    font-size: 0.6875rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  .live .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
  }

  .mark.help-mark,
  .mark.close-mark {
    position: absolute;
    top: 10px;
    right: 10px;
  }

  h4,
  h5,
  p {
    margin: 0;
  }

  .help {
    display: grid;
    place-items: center;
    width: 2.25rem;
    height: 2.25rem;
    border-radius: 50%;
    border: 1px solid var(--odds-overlay-edge);
    background: var(--odds-overlay-bg);
    color: var(--odds-overlay-ink);
    font-weight: 700;
  }

  .help.solid {
    border-color: var(--pill-border);
    background: var(--pill-bg);
    color: var(--pill-ink);
  }

  .content {
    display: grid;
    gap: 12px;
    padding: 16px 14px 0;
  }

  h4 {
    font-family: var(--font-display);
    font-size: 1.375rem;
    font-weight: var(--display-weight);
    letter-spacing: var(--display-tracking);
    color: var(--ink);
  }

  .center {
    justify-self: center;
  }

  .odds {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .cell {
    display: grid;
    gap: 7px;
    min-width: 0;
  }

  .odd {
    display: grid;
    justify-items: center;
    gap: 2px;
    padding: 10px 4px 8px;
    border-radius: var(--radius-m);
    background: var(--pill-bg);
    color: var(--pill-ink);
  }

  .name {
    font-size: 0.75rem;
    font-weight: 500;
  }

  .value {
    font-family: var(--font-display);
    font-size: 1.375rem;
    font-weight: var(--display-weight);
    line-height: 1.1;
  }

  .value small {
    font-size: 0.6em;
    margin-left: 1px;
  }

  .bar {
    display: block;
    height: 5px;
    border-radius: 999px;
    background: var(--track);
    overflow: hidden;
  }

  .bar i {
    display: block;
    height: 100%;
    background: var(--prob-high);
  }

  .more {
    display: grid;
    justify-items: center;
    margin: 12px 14px 0;
    padding: 12px 0;
    border-top: 1px solid var(--line);
  }

  .see-all {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--link);
    font-size: 0.875rem;
    font-weight: 700;
  }

  .back {
    display: grid;
    gap: 10px;
    padding: 16px 56px 18px 18px;
  }

  .eyebrow {
    font-size: 0.6875rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--prob-high);
  }

  .back-title {
    font-size: 1.375rem;
  }

  .back-section {
    display: grid;
    justify-items: start;
    gap: 6px;
    padding-top: 8px;
    border-top: 1px solid var(--line);
  }

  h5 {
    font-size: 0.6875rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }

  .row {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--ink);
    font-size: 0.875rem;
  }

  .line {
    display: block;
    justify-self: stretch;
    width: 85%;
    height: 8px;
    border-radius: 4px;
    background: var(--track);
  }

  .line.short {
    width: 40%;
  }

  /* Numbered marks */
  .mark {
    position: relative;
    display: inline-flex;
    align-items: center;
    max-width: 100%;
  }

  .mark.block {
    display: grid;
  }

  .pin {
    position: absolute;
    top: -9px;
    right: -9px;
    z-index: 2;
    display: grid;
    place-items: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: 2px solid var(--surface);
    background: var(--brand);
    color: var(--on-brand);
    font-size: 0.625rem;
    font-style: normal;
    font-weight: 800;
    line-height: 1;
  }

  /* Beside the section headings of the back, not over their last letter. */
  .back-section .pin {
    top: -3px;
    right: -24px;
  }

  .pin.left {
    right: auto;
    left: -12px;
  }

  .pin.small {
    top: -6px;
    right: -20px;
  }

  .pin.low {
    top: -6px;
  }

  /* Badge legend */
  .legend {
    display: grid;
    gap: 14px;
  }

  .legend ul {
    display: grid;
    gap: 8px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .legend li {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 0.9375rem;
    color: var(--ink);
  }

  .hours {
    color: var(--ink-soft);
    font-variant-numeric: tabular-nums;
  }
</style>
