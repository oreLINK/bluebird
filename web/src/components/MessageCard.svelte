<!-- White card for loading, empty and error states. -->
<script lang="ts">
  import type { Snippet } from 'svelte';
  import Icon from './Icon.svelte';

  let {
    icon = 'info',
    message,
    action,
  }: { icon?: string; message: string; action?: Snippet } = $props();
</script>

<div class="card-body message" role="status">
  <span class="icon"><Icon name={icon} size={24} /></span>
  <p>{message}</p>
  {#if action}{@render action()}{/if}
</div>

<style>
  .message {
    display: grid;
    justify-items: center;
    gap: 12px;
    margin-top: 14px;
    padding: 28px 20px;
    text-align: center;
    color: var(--ink-soft);
  }

  .icon {
    color: var(--prob-high);
  }

  p {
    max-width: 32ch;
  }
</style>
