<!--
  Side menu (opened from the header button): massif and language choices.
  While open, the page behind is blurred, cannot scroll (lib/scrollLock.ts)
  and is made inert by App.svelte, so keyboard focus stays in the menu.
  Closes with Escape, the close button, a tap on the backdrop, or after
  choosing a massif. Focus returns to the element that opened it.
-->
<script lang="ts">
  import { prefersReducedMotion } from 'svelte/motion';
  import { fade, fly } from 'svelte/transition';
  import type { Massif } from '../lib/config';
  import { LOCALES, LOCALE_NAMES } from '../lib/i18n/core';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { lockScroll, unlockScroll } from '../lib/scrollLock';
  import Icon from './Icon.svelte';

  let {
    open,
    onclose,
    massifs,
    selectedMassif,
    onselectmassif,
  }: {
    open: boolean;
    onclose: () => void;
    massifs: Massif[];
    selectedMassif: string;
    onselectmassif: (id: string) => void;
  } = $props();

  let closeButton = $state<HTMLButtonElement>();
  const duration = $derived(prefersReducedMotion.current ? 0 : 220);

  $effect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    lockScroll();
    closeButton?.focus();
    return () => {
      unlockScroll();
      requestAnimationFrame(() => previous?.focus());
    };
  });

  function onkeydown(event: KeyboardEvent) {
    if (open && event.key === 'Escape') {
      event.preventDefault();
      onclose();
    }
  }
</script>

<svelte:window {onkeydown} />

{#if open}
  <div class="backdrop" transition:fade={{ duration }} onclick={onclose} aria-hidden="true"></div>
  <div
    class="panel"
    role="dialog"
    aria-modal="true"
    aria-labelledby="menu-title"
    transition:fly={{ x: 360, duration, opacity: 1 }}
  >
    <header class="panel-head">
      <h2 id="menu-title">{i18n.t('menu.title')}</h2>
      <button
        bind:this={closeButton}
        type="button"
        class="close"
        aria-label={i18n.t('menu.close')}
        onclick={onclose}
      >
        <Icon name="close" size={22} />
      </button>
    </header>

    <section aria-labelledby="menu-massif">
      <h3 id="menu-massif"><Icon name="mountain" size={16} />{i18n.t('menu.massif')}</h3>
      <ul>
        {#each massifs as massif (massif.id)}
          <li>
            <button
              type="button"
              class="option"
              aria-pressed={massif.id === selectedMassif}
              onclick={() => onselectmassif(massif.id)}
            >
              <span>{i18n.pick(massif.name)}</span>
              {#if massif.id === selectedMassif}<Icon name="check" size={18} />{/if}
            </button>
          </li>
        {/each}
      </ul>
    </section>

    <section aria-labelledby="menu-language">
      <h3 id="menu-language"><Icon name="globe" size={16} />{i18n.t('menu.language')}</h3>
      <ul>
        {#each LOCALES as locale (locale)}
          <li>
            <button
              type="button"
              class="option"
              lang={locale}
              aria-pressed={i18n.locale === locale}
              onclick={() => i18n.setLocale(locale)}
            >
              <span>{LOCALE_NAMES[locale]}</span>
              {#if i18n.locale === locale}<Icon name="check" size={18} />{/if}
            </button>
          </li>
        {/each}
      </ul>
    </section>
  </div>
{/if}

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    z-index: 40;
    background: var(--scrim);
    -webkit-backdrop-filter: blur(14px) saturate(120%);
    backdrop-filter: blur(14px) saturate(120%);
  }

  .panel {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    z-index: 41;
    display: grid;
    align-content: start;
    gap: 22px;
    width: min(86vw, 360px);
    padding: max(14px, env(safe-area-inset-top)) max(18px, env(safe-area-inset-right)) 24px 18px;
    overflow-y: auto;
    overscroll-behavior: contain;
    background: var(--surface);
    border-left: 1px solid var(--line);
    box-shadow: -18px 0 40px -20px rgba(4, 14, 32, 0.5);
  }

  .panel-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  h2 {
    font-family: var(--font-display);
    font-size: 1.75rem;
    font-style: italic;
    font-weight: 800;
    color: var(--brand);
  }

  .close {
    display: grid;
    place-items: center;
    width: 44px;
    height: 44px;
    border-radius: var(--radius-s);
    border: 1px solid var(--line);
    background: var(--surface);
    color: var(--ink);
    cursor: pointer;
  }

  h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 8px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }

  ul {
    display: grid;
    gap: 6px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    min-height: 3rem;
    padding: 0 14px;
    border-radius: var(--radius-m);
    border: 1px solid var(--line);
    background: var(--surface-2);
    color: var(--ink);
    font-size: 1rem;
    font-weight: 600;
    text-align: left;
    cursor: pointer;
  }

  .option[aria-pressed='true'] {
    border-color: var(--brand);
    background: var(--brand);
    color: var(--on-brand);
  }

  @media (prefers-reduced-transparency: reduce) {
    .backdrop {
      background: var(--scrim-solid);
      -webkit-backdrop-filter: none;
      backdrop-filter: none;
    }
  }
</style>
