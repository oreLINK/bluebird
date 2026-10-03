<script lang="ts">
  import AppFooter from './components/AppFooter.svelte';
  import AppHeader from './components/AppHeader.svelte';
  import ForecastStatus from './components/ForecastStatus.svelte';
  import Icon from './components/Icon.svelte';
  import MessageCard from './components/MessageCard.svelte';
  import MountainBackdrop from './components/MountainBackdrop.svelte';
  import SnowfallLayer from './components/SnowfallLayer.svelte';
  import { AMBIENT_SNOW_KPI, massifs, tilesForMassif } from './lib/config';
  import { type MassifDaily, loadMassif, maxProbability } from './lib/data';
  import { i18n } from './lib/i18n/i18n.svelte';
  import { readPref, writePref } from './lib/prefs';
  import { tileComponent } from './tiles/registry';
  import TileShell from './tiles/TileShell.svelte';
  import TileSkeleton from './tiles/TileSkeleton.svelte';

  type Status = 'loading' | 'ready' | 'empty' | 'error';

  const stored = readPref('massif');
  let massifId = $state(
    massifs.some((m) => m.id === stored) ? (stored as string) : (massifs[0]?.id ?? ''),
  );
  let status = $state<Status>('loading');
  let payload = $state<MassifDaily | null>(null);
  let attempt = $state(0);

  const massif = $derived(massifs.find((m) => m.id === massifId));
  const resolvedTiles = $derived(tilesForMassif(massifId));
  const snowIntensity = $derived(maxProbability(payload, AMBIENT_SNOW_KPI));

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
  }
</script>

<MountainBackdrop skyline={massif?.skyline ?? []} />
<SnowfallLayer intensity={snowIntensity} />

<AppHeader {massifs} selected={massifId} onselect={selectMassif} />

<main class="container main">
  {#if status === 'ready' && payload}
    <ForecastStatus data={payload} />
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
  {:else}
    <p class="visually-hidden" role="status">
      {status === 'loading' ? i18n.t('status.loading') : ''}
    </p>
    <div class="tiles">
      {#each resolvedTiles as { tile, kpis } (tile.id)}
        {@const title = i18n.pick(tile.title ?? kpis[0]?.name)}
        {@const TileComponent = tileComponent(tile.type)}
        {#if status === 'loading' || !payload}
          <TileSkeleton id={tile.id} {title} icon={tile.icon} />
        {:else if TileComponent}
          <TileComponent {tile} {kpis} data={payload} />
        {:else if import.meta.env.DEV}
          <TileShell id={tile.id} {title} icon={tile.icon}>
            <p>{i18n.t('tile.unsupported', { type: tile.type })}</p>
          </TileShell>
        {/if}
      {/each}
    </div>
  {/if}
</main>

<AppFooter data={payload} />

<style>
  .main {
    position: relative;
    z-index: 1;
    padding-bottom: 20px;
  }

  .tagline {
    padding: 18px 4px 14px;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--ink-on-sky);
  }

  .tiles {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 16px;
    align-items: start;
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
    background: var(--accent);
    color: var(--accent-ink);
    font-weight: 650;
    cursor: pointer;
  }
</style>
