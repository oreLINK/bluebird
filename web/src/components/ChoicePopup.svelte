<!--
  Choice popup shared by the header buttons (language, appearance): a small
  card under the button lists the options (a leading visual, a name, a check
  on the current one); choosing one calls `onchoose` and closes the popup.
  While open, the page behind is blurred, cannot scroll (lib/scrollLock.ts)
  and is made inert by App.svelte, so keyboard focus stays in the popup.
  Closes with Escape, the close button or a tap on the backdrop; focus returns
  to the button that opened it.
-->
<script lang="ts" generics="Id extends string">
  import type { Snippet } from 'svelte';
  import { prefersReducedMotion } from 'svelte/motion';
  import { fade, scale } from 'svelte/transition';
  import { lockScroll, unlockScroll } from '../lib/scrollLock';
  import Icon from './Icon.svelte';

  let {
    open,
    onclose,
    id,
    title,
    titleIcon,
    closeLabel,
    options,
    current,
    onchoose,
    lead,
  }: {
    open: boolean;
    onclose: () => void;
    /** DOM id prefix (title: `<id>-title`). */
    id: string;
    title: string;
    titleIcon: string;
    closeLabel: string;
    options: { id: Id; label: string; lang?: string }[];
    current: Id;
    onchoose: (id: Id) => void;
    /** Leading visual of an option (a flag, an icon). */
    lead: Snippet<[Id]>;
  } = $props();

  let currentButton = $state<HTMLButtonElement>();
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
    currentButton?.focus();
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

  function choose(value: Id) {
    onchoose(value);
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
    aria-labelledby="{id}-title"
    transition:scale={{ start: 0.92, duration, opacity: 0 }}
  >
    <header class="head">
      <h2 id="{id}-title"><Icon name={titleIcon} size={18} />{title}</h2>
      <button type="button" class="close" aria-label={closeLabel} onclick={onclose}>
        <Icon name="close" size={20} />
      </button>
    </header>
    <ul>
      {#each options as option (option.id)}
        <li>
          {#if option.id === current}
            <button
              bind:this={currentButton}
              type="button"
              class="option"
              lang={option.lang}
              aria-pressed="true"
              onclick={() => choose(option.id)}
            >
              {@render lead(option.id)}
              <span class="name">{option.label}</span>
              <Icon name="check" size={18} />
            </button>
          {:else}
            <button
              type="button"
              class="option"
              lang={option.lang}
              aria-pressed="false"
              onclick={() => choose(option.id)}
            >
              {@render lead(option.id)}
              <span class="name">{option.label}</span>
            </button>
          {/if}
        </li>
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
