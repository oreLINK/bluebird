<!--
  Sticky app bar on frosted white: logo and title on the left, menu button on
  the right; below, the massif bar (place levels of lib/geoLevels.ts:
  massif, département, linked area), then the filter bar (filter levels of
  lib/filterLevels.ts), both with the same chips.
-->
<script lang="ts">
  import type { FilterChip } from '../lib/filterLevels';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import FilterBar from './FilterBar.svelte';
  import Icon from './Icon.svelte';
  import Logo from './Logo.svelte';

  let {
    places,
    onselectplace,
    filters,
    onselectfilter,
    menuOpen,
    onmenu,
  }: {
    places: FilterChip[];
    /** Called with the chip `key`. */
    onselectplace: (key: string) => void;
    filters: FilterChip[];
    /** Called with the chip `key`. */
    onselectfilter: (key: string) => void;
    menuOpen: boolean;
    onmenu: () => void;
  } = $props();
</script>

<header class="header glass">
  <div class="container inner">
    <div class="top">
      <h1 class="brand"><Logo /></h1>
      <button
        type="button"
        class="menu-button"
        aria-label={i18n.t('menu.open')}
        aria-haspopup="dialog"
        aria-expanded={menuOpen}
        onclick={onmenu}
      >
        <Icon name="menu" size={24} />
      </button>
    </div>
    <div class="bars">
      {#if places.length > 0}
        <FilterBar
          options={places.map((c) => ({ ...c, removable: c.pressed }))}
          onselect={onselectplace}
          resetScroll
          label={i18n.t('massifs.label')}
        />
      {/if}
      {#if filters.length > 0}
        <FilterBar
          options={filters.map((c) => ({ ...c, removable: c.pressed }))}
          onselect={onselectfilter}
          resetScroll
          label={i18n.t('filters.label')}
        />
      {/if}
    </div>
  </div>
</header>

<style>
  .header {
    position: sticky;
    top: 0;
    z-index: 10;
    padding-top: env(safe-area-inset-top);
  }

  .inner {
    display: grid;
    gap: 10px;
    padding-top: 10px;
    padding-bottom: 10px;
  }

  .bars {
    display: grid;
    gap: 6px;
  }

  .top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .brand {
    display: flex;
    min-width: 0;
  }

  .menu-button {
    display: grid;
    place-items: center;
    flex: none;
    width: 44px;
    height: 44px;
    border-radius: var(--radius-s);
    border: 1px solid var(--line);
    background: var(--surface);
    color: var(--brand);
    cursor: pointer;
  }
</style>
