<!--
  Inline stroke icons (24x24). Tiles reference them by name from
  config/tiles.yaml (`icon:`). Add a case below to add an icon.
-->
<script lang="ts">
  let { name, size = 20, class: className = '' }: { name: string; size?: number; class?: string } =
    $props();
</script>

<svg
  class={className}
  width={size}
  height={size}
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="1.8"
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-hidden="true"
>
  {#if name === 'snowflake'}
    <path d="M12 2v20M3.3 7l17.4 10M3.3 17 20.7 7" />
    <path d="m9.5 3.8 2.5 2.4 2.5-2.4M9.5 20.2l2.5-2.4 2.5 2.4" />
    <path d="m4.4 10.6 3.3-1-.8-3.3M19.6 13.4l-3.3 1 .8 3.3" />
    <path d="m6.9 17.7.8-3.3-3.3-1M17.1 6.3l-.8 3.3 3.3 1" />
  {:else if name === 'mountain'}
    <path d="M2.5 20 9 8.5l3.6 6.1 2.2-3.4L21.5 20Z" />
    <path d="m7.1 11.9 1.9 1.3 1.6-1.6" />
  {:else if name === 'piste'}
    <path d="M6 21c3.5-5 5.2-10.5 5.8-18" />
    <path d="M12.5 21c2.8-4.6 4.3-9.6 4.8-18" />
    <path d="M4 7.5h3.5M17.5 11H21" />
  {:else if name === 'chevron'}
    <path d="m6 9 6 6 6-6" />
  {:else if name === 'info'}
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5.5M12 7.5v.01" />
  {:else if name === 'menu'}
    <path d="M4 7h16M4 12h16M4 17h10" />
  {:else if name === 'close'}
    <path d="M6 6l12 12M18 6 6 18" />
  {:else if name === 'check'}
    <path d="m5 12.5 4.5 4.5L19 7.5" />
  {:else if name === 'sparkle'}
    <path d="M12 3.5c.6 3.9 2.6 5.9 6.5 6.5-3.9.6-5.9 2.6-6.5 6.5-.6-3.9-2.6-5.9-6.5-6.5 3.9-.6 5.9-2.6 6.5-6.5Z" />
    <path d="M18.5 15.5c.3 1.5 1 2.2 2.5 2.5-1.5.3-2.2 1-2.5 2.5-.3-1.5-1-2.2-2.5-2.5 1.5-.3 2.2-1 2.5-2.5Z" />
  {:else if name === 'globe'}
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18M12 3c2.5 2.6 3.7 5.6 3.7 9S14.5 18.4 12 21c-2.5-2.6-3.7-5.6-3.7-9S9.5 5.6 12 3Z" />
  {:else if name === 'refresh'}
    <path d="M20 11a8 8 0 1 0-2.3 5.7" />
    <path d="M20 4v7h-7" />
  {:else}
    <circle cx="12" cy="12" r="3" />
  {/if}
</svg>
