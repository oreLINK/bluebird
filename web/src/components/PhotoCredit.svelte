<!-- Credit line of a banner photo ("Photo: author (licence)"), linked when a source URL exists. -->
<script lang="ts">
  import { i18n } from '../lib/i18n/i18n.svelte';
  import type { PhotoCredit } from '../lib/photos';

  let { credit, class: className = '' }: { credit: PhotoCredit; class?: string } = $props();

  const text = $derived(
    i18n.t('photo.credit', {
      author: credit.license ? `${credit.author} (${credit.license})` : credit.author,
    }),
  );
</script>

{#if credit.url}
  <a class="credit {className}" href={credit.url} target="_blank" rel="noopener noreferrer">{text}</a>
{:else}
  <span class="credit {className}">{text}</span>
{/if}

<style>
  .credit {
    display: inline-block;
    max-width: 100%;
    padding: 2px 6px;
    border-radius: 6px;
    background: var(--banner-label-bg);
    color: #ffffff;
    font-size: 0.625rem;
    line-height: 1.3;
    text-decoration: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
</style>
