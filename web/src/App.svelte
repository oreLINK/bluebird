<script lang="ts">
  import AppFooter from './components/AppFooter.svelte';
  import AppHeader from './components/AppHeader.svelte';
  import AppMenu from './components/AppMenu.svelte';
  import ForecastStatus from './components/ForecastStatus.svelte';
  import Icon from './components/Icon.svelte';
  import InfoPage from './components/InfoPage.svelte';
  import MessageCard from './components/MessageCard.svelte';
  import {
    filterTiles,
    filters,
    massifs,
    pages,
    rewindOfFilter,
    rewindPayload,
    rewinds,
    tilesForMassif,
    usableFilters,
  } from './lib/config';
  import { type MassifDaily, type ServiceStatus, loadMassif, loadStatus } from './lib/data';
  import { i18n } from './lib/i18n/i18n.svelte';
  import { readPref, writePref } from './lib/prefs';
  import { sheets } from './lib/sheets.svelte';
  import { arrive, leave, motion } from './lib/transitions';
  import { flip } from 'svelte/animate';
  import { viewFor } from './lib/kpiView';
  import { expandTiles, instanceTitle, isLiveTile, nextBoundary } from './lib/periods';
  import { skeletonVariant, tileComponent } from './tiles/registry';
  import TileShell from './tiles/TileShell.svelte';
  import TileSkeleton from './tiles/TileSkeleton.svelte';

  type Status = 'loading' | 'ready' | 'empty' | 'error';

  const storedMassif = readPref('massif');
  let massifId = $state(
    massifs.some((m) => m.id === storedMassif) ? (storedMassif as string) : (massifs[0]?.id ?? ''),
  );
  let filterId = $state(readPref('filter') ?? '');
  let menuOpen = $state(false);
  let status = $state<Status>('loading');
  let payload = $state<MassifDaily | null>(null);
  let serviceStatus = $state<ServiceStatus | null>(null);
  let attempt = $state(0);
  /** The visitor's clock: periods disappear when they end, without a reload. */
  let now = $state(Date.now());

  const resolvedTiles = $derived(tilesForMassif(massifId));
  /** A full-window page is open (`#<page id>` in the URL): the page behind is inert. */
  const sheetOpen = $derived(pages.some((p) => p.id === sheets.current));
  const barFilters = $derived(usableFilters(filters, resolvedTiles));
  const activeFilter = $derived(barFilters.find((f) => f.id === filterId) ?? barFilters[0]);
  const visibleTiles = $derived(filterTiles(resolvedTiles, activeFilter, barFilters));
  /** The Rewind of the active filter: its tiles do not depend on the live forecasts. */
  const activeRewind = $derived(rewindOfFilter(activeFilter?.id));
  const showsLive = $derived(visibleTiles.some(isLiveTile));
  /** One tile per live tile and period not over yet, then the Rewind tiles. */
  const instances = $derived(expandTiles(visibleTiles, payload, now));
  const massif = $derived(massifs.find((m) => m.id === massifId));

  $effect(() => {
    const id = massifId;
    void attempt; // re-run on retry
    let cancelled = false;
    status = 'loading';
    payload = null;
    loadMassif(id)
      .then((result) => {
        if (cancelled) return;
        payload = result;
        status = result ? 'ready' : 'empty';
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        console.error(error);
        status = 'error';
      });
    return () => {
      cancelled = true;
    };
  });

  $effect(() => {
    void attempt; // re-run on retry
    let cancelled = false;
    loadStatus()
      .then((result) => {
        if (!cancelled) serviceStatus = result;
      })
      .catch((error: unknown) => {
        console.error(error); // the footer says the status is unavailable
        if (!cancelled) serviceStatus = null;
      });
    return () => {
      cancelled = true;
    };
  });

  // Tick the clock when the next visible period ends, every minute, and when
  // the tab comes back to the foreground.
  $effect(() => {
    const tick = () => (now = Date.now());
    const next = nextBoundary(payload, now);
    const timeout = next === null ? undefined : setTimeout(tick, Math.max(0, next - now) + 250);
    const interval = setInterval(tick, 60_000);
    const onVisible = () => {
      if (!document.hidden) tick();
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      clearTimeout(timeout);
      clearInterval(interval);
      document.removeEventListener('visibilitychange', onVisible);
    };
  });

  $effect(() => {
    document.documentElement.lang = i18n.locale;
  });

  function selectMassif(id: string) {
    massifId = id;
    writePref('massif', id);
  }

  function selectFilter(id: string) {
    filterId = id;
    writePref('filter', id);
  }

</script>

<div class="page" inert={menuOpen || sheetOpen}>
  <AppHeader
    {massifs}
    selectedMassif={massifId}
    onselectmassif={selectMassif}
    filters={barFilters}
    selectedFilter={activeFilter?.id ?? ''}
    onselectfilter={selectFilter}
    {menuOpen}
    onmenu={() => (menuOpen = true)}
  />

  <main class="container main">
    {#if activeRewind}
      <ForecastStatus rewind={activeRewind} />
    {:else if status === 'ready' && payload}
      <ForecastStatus data={payload} {now} />
    {:else}
      <p class="tagline">{i18n.t('app.tagline')}</p>
    {/if}

    {#if showsLive && status === 'empty'}
      <MessageCard icon="snowflake" message={i18n.t('status.noData')} />
    {:else if showsLive && status === 'error'}
      <MessageCard message={i18n.t('status.error')}>
        {#snippet action()}
          <button type="button" class="retry" onclick={() => attempt++}>
            <Icon name="refresh" size={18} />
            {i18n.t('status.retry')}
          </button>
        {/snippet}
      </MessageCard>
    {:else if visibleTiles.length === 0}
      <MessageCard icon="info" message={i18n.t('filter.empty')} />
    {:else if showsLive && status === 'loading'}
      <p class="visually-hidden" role="status">{i18n.t('status.loading')}</p>
      <div class="tiles">
        {#each visibleTiles as { tile, kpis } (tile.id)}
          <div class="slot">
            <TileSkeleton
              id={tile.id}
              title={i18n.pick(instanceTitle(tile, kpis, { fr: '', en: '' })).trim()}
              icon={tile.icon}
              variant={skeletonVariant(tile.type)}
            />
          </div>
        {/each}
      </div>
    {:else if instances.length === 0}
      <MessageCard icon="info" message={i18n.t('tiles.allOver')} />
    {:else}
      <div class="tiles">
        {#each instances as instance, index (instance.id)}
          {@const { tile, kpis, slot } = instance}
          {@const TileComponent = tileComponent(tile.type)}
          {@const view = viewFor(kpis[0], massifId, payload, rewinds, rewindPayload, slot)}
          <div
            class="slot"
            animate:flip={{ duration: motion(260) }}
            in:arrive={{ delay: Math.min(index, 8) * 45 }}
            out:leave
          >
            {#if !view}
              <TileSkeleton
                id={tile.id}
                title={i18n.pick(tile.title ?? kpis[0]?.name)}
                icon={tile.icon}
                variant={skeletonVariant(tile.type)}
              />
            {:else if TileComponent}
              <TileComponent {tile} {kpis} {view} />
            {:else if import.meta.env.DEV}
              <TileShell id={tile.id} title={i18n.pick(tile.title ?? kpis[0]?.name)} icon={tile.icon}>
                <p>{i18n.t('tile.unsupported', { type: tile.type })}</p>
              </TileShell>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </main>

  <AppFooter
    status={serviceStatus}
    {massifId}
    timezone={payload?.timezone ?? massif?.timezone ?? 'Europe/Paris'}
    {now}
  />
</div>

<AppMenu open={menuOpen} onclose={() => (menuOpen = false)} />

{#each pages as page (page.id)}
  <InfoPage {page} />
{/each}

<style>
  .main {
    padding-bottom: 20px;
  }

  .tagline {
    padding: 18px 4px 14px;
    font-size: 1.0625rem;
    font-weight: 700;
    color: var(--ink-soft);
  }

  .tiles {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 18px;
    align-items: start;
  }

  .slot {
    min-width: 0;
    transform-origin: 50% 40%;
  }

  @media (min-width: 768px) {
    .tiles {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (min-width: 1100px) {
    .tiles {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }

  .retry {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-height: 2.75rem;
    padding: 0 18px;
    border: 0;
    border-radius: 999px;
    background: var(--brand);
    color: var(--on-brand);
    font-weight: 650;
    cursor: pointer;
  }
</style>
