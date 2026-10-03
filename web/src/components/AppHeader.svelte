<script lang="ts">
  import type { Massif } from '../lib/config';
  import LangToggle from './LangToggle.svelte';
  import MassifPicker from './MassifPicker.svelte';

  let {
    massifs,
    selected,
    onselect,
  }: { massifs: Massif[]; selected: string; onselect: (id: string) => void } = $props();
</script>

<header class="header">
  <div class="container">
    <div class="bar glass glass-strong">
      <div class="top">
        <h1 class="brand">
          <svg class="mark" viewBox="0 0 32 32" aria-hidden="true">
            <defs>
              <linearGradient id="bb-mark" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stop-color="#0a4aa6" />
                <stop offset="1" stop-color="#5aa8ec" />
              </linearGradient>
            </defs>
            <rect width="32" height="32" rx="9" fill="url(#bb-mark)" />
            <circle cx="23" cy="9.5" r="3" fill="#ffe28a" />
            <path d="M3 27 12.5 12l4.6 7 2.6-3.6L29 27Z" fill="#fff" />
            <path d="m9.7 16.4 2.8 1.6 2.3-1.8" fill="none" stroke="#bcd8f3" stroke-width="1.2" />
          </svg>
          <span>Bluebird</span>
        </h1>
        <LangToggle />
      </div>
      <MassifPicker {massifs} {selected} {onselect} />
    </div>
  </div>
</header>

<style>
  .header {
    position: sticky;
    top: 0;
    z-index: 10;
    padding-top: max(10px, env(safe-area-inset-top));
  }

  .bar {
    display: grid;
    gap: 10px;
    padding: 10px 12px 12px;
    border-radius: 24px;
  }

  .top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    font-size: 1.25rem;
    font-weight: 750;
    letter-spacing: -0.025em;
  }

  .mark {
    width: 32px;
    height: 32px;
    flex: none;
  }
</style>
