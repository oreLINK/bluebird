<!--
  Generic full-window sheet ("over-page"): covers the whole window with a
  strong Liquid Glass surface (the page behind is heavily blurred), a title
  and a close button in the top-right corner, and scrollable content.
  It rises from the bottom when it opens and slides back down when it closes
  (lib/transitions.ts `rise`, instant with reduced motion).
  While open, page scrolling is locked (lib/scrollLock.ts) and App.svelte
  makes the page inert. Closes with Escape or the close button; focus goes
  to the close button, then back to the element that opened it.
  Open state usually comes from lib/sheets.svelte.ts (`#<id>` in the URL).

  <Sheet id="legal" title="Mentions légales" open={…} onclose={…}>…</Sheet>
-->
<script lang="ts">
  import type { Snippet } from 'svelte';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { lockScroll, unlockScroll } from '../lib/scrollLock';
  import { rise } from '../lib/transitions';
  import Icon from './Icon.svelte';

  let {
    id,
    title,
    open,
    onclose,
    children,
  }: {
    id: string;
    title: string;
    open: boolean;
    onclose: () => void;
    children: Snippet;
  } = $props();

  let closeButton = $state<HTMLButtonElement>();
  /** Element that had focus before opening (the footer link…), focused again on close. */
  let opener: HTMLElement | null = null;

  // Before the DOM update: once the sheet renders, App.svelte makes the page
  // inert, which blurs the opener.
  $effect.pre(() => {
    if (open) opener = document.activeElement as HTMLElement | null;
  });

  $effect(() => {
    if (!open) return;
    lockScroll();
    closeButton?.focus({ preventScroll: true });
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
</script>

<svelte:window {onkeydown} />

{#if open}
  <div
    class="sheet"
    role="dialog"
    aria-modal="true"
    aria-labelledby="{id}-sheet-title"
    transition:rise
  >
    <header class="head">
      <div class="head-inner">
        <h2 id="{id}-sheet-title">{title}</h2>
        <button
          bind:this={closeButton}
          type="button"
          class="close"
          aria-label={i18n.t('sheet.close')}
          onclick={onclose}
        >
          <Icon name="close" size={22} />
        </button>
      </div>
    </header>
    <div class="scroll">
      <div class="content">
        {@render children()}
      </div>
    </div>
  </div>
{/if}

<style>
  .sheet {
    position: fixed;
    inset: 0;
    z-index: 50;
    display: flex;
    flex-direction: column;
    background: var(--sheet-bg);
    -webkit-backdrop-filter: blur(var(--sheet-blur)) saturate(170%);
    backdrop-filter: blur(var(--sheet-blur)) saturate(170%);
    color: var(--ink);
  }

  .head {
    flex: none;
    padding: max(12px, env(safe-area-inset-top)) max(var(--gutter), env(safe-area-inset-right)) 10px
      max(var(--gutter), env(safe-area-inset-left));
    border-bottom: 1px solid var(--glass-border);
  }

  .head-inner,
  .content {
    width: 100%;
    max-width: 720px;
    margin: 0 auto;
  }

  .head-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  h2 {
    min-width: 0;
    font-family: var(--font-display);
    font-size: 1.875rem;
    font-style: italic;
    font-weight: 800;
    line-height: 1.1;
    color: var(--brand);
  }

  .close {
    display: grid;
    place-items: center;
    flex: none;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: 1px solid var(--line);
    background: var(--surface);
    color: var(--ink);
    cursor: pointer;
  }

  .scroll {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overscroll-behavior: contain;
    padding: 6px max(var(--gutter), env(safe-area-inset-right))
      max(32px, env(safe-area-inset-bottom)) max(var(--gutter), env(safe-area-inset-left));
  }

  @supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
    .sheet {
      background: var(--glass-solid);
    }
  }

  @media (prefers-reduced-transparency: reduce) {
    .sheet {
      background: var(--glass-solid);
      -webkit-backdrop-filter: none;
      backdrop-filter: none;
    }
  }
</style>
