<script lang="ts">
  import AppFooter from './components/AppFooter.svelte';
  import AppHeader from './components/AppHeader.svelte';
  import AppMenu from './components/AppMenu.svelte';
  import ForecastStatus from './components/ForecastStatus.svelte';
  import Icon from './components/Icon.svelte';
  import MessageCard from './components/MessageCard.svelte';
  import { filterTiles, filters, massifs, tilesForMassif, usableFilters } from './lib/config';
  import { type MassifDaily, loadMassif } from './lib/data';
  import { i18n } from './lib/i18n/i18n.svelte';
  import { readPref, writePref } from './lib/prefs';
  import { arrive, leave, motion } from './lib/transitions';
  import { flip } from 'svelte/animate';
  import { tileComponent } from './tiles/registry';
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
  let attempt = $state(0);

  const massif = $derived(massifs.find((m) => m.id === massifId));
  const resolvedTiles = $derived(tilesForMassif(massifId));
  const barFilters = $derived(usableFilters(filters, resolvedTiles));
  const activeFilter = $derived(barFilters.find((f) => f.id === filterId) ?? barFilters[0]);
  const visibleTiles = $derived(filterTiles(resolvedTiles, activeFilter));

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
    document.documentElement.lang = i18n.locale;
  });

  function selectMassif(id: string) {
    massifId = id;
    writePref('massif', id);
    menuOpen = false;
  }

  function selectFilter(id: string) {
    filterId = id;
    writePref('filter', id);
  }

  function skeletonVariant(type: string): 'banner' | 'full' | 'list' {
    if (type === 'banner_full') return 'full';
    return type === 'banner' ? 'banner' : 'list';
  }
</script>

<div class="page" inert={menuOpen}>
  <AppHeader
    filters={barFilters}
    selectedFilter={activeFilter?.id ?? ''}
    onselectfilter={selectFilter}
    {menuOpen}
    onmenu={() => (menuOpen = true)}
  />

  <main class="container main">
    {#if status === 'ready' && payload}
      <ForecastStatus data={payload} massifName={i18n.pick(massif?.name)} />
    {:else}
      <p class="tagline">{i18n.t('app.tagline')}</p>
    {/if}

    {#if status === 'empty'}
      <MessageCard icon="snowflake" message={i18n.t('status.noData')} />
    {:else if status === 'error'}
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
    {:else}
      <p class="visually-hidden" role="status">
        {status === 'loading' ? i18n.t('status.loading') : ''}
      </p>
      <div class="tiles">
        {#each visibleTiles as { tile, kpis }, index (tile.id)}
          {@const title = i18n.pick(tile.title ?? kpis[0]?.name)}
          {@const TileComponent = tileComponent(tile.type)}
          <div
            class="slot"
            animate:flip={{ duration: motion(260) }}
            in:arrive={{ delay: index * 45 }}
            out:leave
          >
            {#if status === 'loading' || !payload}
              <TileSkeleton
                id={tile.id}
                {title}
                icon={tile.icon}
                variant={skeletonVariant(tile.type)}
              />
            {:else if TileComponent}
              <TileComponent {tile} {kpis} data={payload} />
            {:else if import.meta.env.DEV}
              <TileShell id={tile.id} {title} icon={tile.icon}>
                <p>{i18n.t('tile.unsupported', { type: tile.type })}</p>
              </TileShell>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </main>

  <AppFooter data={payload} />
</div>

<AppMenu
  open={menuOpen}
  onclose={() => (menuOpen = false)}
  {massifs}
  selectedMassif={massifId}
  onselectmassif={selectMassif}
/>

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
