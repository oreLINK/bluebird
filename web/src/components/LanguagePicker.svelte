<!--
  Language popup, opened from the flag button at the top right of the header.
  A small card under the button lists the languages (flag and name in the
  language itself); choosing one switches the site and closes the popup.
  The default language follows the browser (detectLocale in lib/i18n/core.ts)
  until the visitor picks one, which is then remembered.
  While open, the page behind is blurred, cannot scroll (lib/scrollLock.ts)
  and is made inert by App.svelte, so keyboard focus stays in the popup.
  Closes with Escape, the close button or a tap on the backdrop; focus returns
  to the flag button.
-->
<script lang="ts">
  import { prefersReducedMotion } from 'svelte/motion';
  import { fade, scale } from 'svelte/transition';
  import { LOCALES, LOCALE_FLAGS, LOCALE_NAMES, type Locale } from '../lib/i18n/core';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { lockScroll, unlockScroll } from '../lib/scrollLock';
  import Flag from './Flag.svelte';
  import Icon from './Icon.svelte';

  let { open, onclose }: { open: boolean; onclose: () => void } = $props();

  let current = $state<HTMLButtonElement>();
  const duration = $derived(prefersReducedMotion.current ? 0 : 180);

  let opener: HTMLElement | null = null;

  // Before the DOM update: once the popup renders, App.svelte makes the page
  // inert, which blurs the opener (CONTEXT.md §8).
  $effect.pre(() => {
    if (open) opener = document.activeElement as HTMLElement | null;
  });

  $effect(() => {
    if (!open) return;
    lockScroll();
    current?.focus();
    return () => {
      unlockScroll();
      const target = opener;
      requestAnimationFrame(() => target?.focus({ preventScroll: true }));
    };
  });

  function onkeydown(event: KeyboardEvent) {
    if (open && event.key === 'Escape') {
      event.preventDefault();
      onclose();
    }
  }

  function choose(locale: Locale) {
    i18n.setLocale(locale);
    onclose();
  }
</script>

<svelte:window {onkeydown} />

{#if open}
  <div class="backdrop" transition:fade={{ duration }} onclick={onclose} aria-hidden="true"></div>
  <div
    class="popup"
    role="dialog"
    aria-modal="true"
    aria-labelledby="language-title"
    transition:scale={{ start: 0.92, duration, opacity: 0 }}
  >
    <header class="head">
      <h2 id="language-title"><Icon name="globe" size={18} />{i18n.t('language.title')}</h2>
      <button type="button" class="close" aria-label={i18n.t('language.close')} onclick={onclose}>
        <Icon name="close" size={20} />
      </button>
    </header>
    <ul>
      {#each LOCALES as locale (locale)}
        {#if i18n.locale === locale}
          <li>
            <button
              bind:this={current}
              type="button"
              class="option"
              lang={locale}
              aria-pressed="true"
              onclick={() => choose(locale)}
            >
              <Flag country={LOCALE_FLAGS[locale]} width={30} />
              <span class="name">{LOCALE_NAMES[locale]}</span>
              <Icon name="check" size={18} />
            </button>
          </li>
        {:else}
          <li>
            <button
              type="button"
              class="option"
              lang={locale}
              aria-pressed="false"
              onclick={() => choose(locale)}
            >
              <Flag country={LOCALE_FLAGS[locale]} width={30} />
              <span class="name">{LOCALE_NAMES[locale]}</span>
            </button>
          </li>
        {/if}
      {/each}
    </ul>
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

  .popup {
    position: fixed;
    top: calc(env(safe-area-inset-top) + 62px);
    right: max(var(--gutter), env(safe-area-inset-right));
    z-index: 41;
    display: grid;
    gap: 12px;
    width: min(280px, calc(100vw - 2 * var(--gutter)));
    padding: 14px;
    box-sizing: border-box;
    border-radius: var(--radius-l);
    border: 1px solid var(--line);
    background: var(--surface);
    box-shadow: 0 18px 40px -18px rgba(4, 14, 32, 0.55);
    transform-origin: top right;
  }

  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  h2 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
    font-family: var(--font-display);
    letter-spacing: var(--display-tracking);
    font-size: 1.5rem;
    font-weight: var(--display-weight);
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
    gap: 12px;
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

  .name {
    flex: 1;
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
