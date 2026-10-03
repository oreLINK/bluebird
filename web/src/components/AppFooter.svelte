<script lang="ts">
  import type { MassifDaily } from '../lib/data';
  import { i18n } from '../lib/i18n/i18n.svelte';

  let { data }: { data: MassifDaily | null } = $props();
</script>

<footer class="container footer">
  <div class="card-body box">
    <p class="method">{i18n.t('footer.method')}</p>
    <p class="disclaimer">
      {i18n.t('footer.disclaimer')}
      <a href="https://meteofrance.com/meteo-montagne" target="_blank" rel="noopener noreferrer">
        {i18n.t('footer.bera')}
      </a>
    </p>
    {#if data && data.sources.length > 0}
      <p class="sources">
        <span>{i18n.t('footer.sources')} :</span>
        {#each data.sources as source, i (source.id)}
          <a href={source.url} target="_blank" rel="noopener noreferrer">{source.name}</a
          >{#if source.license}&nbsp;({source.license}){/if}{#if i < data.sources.length - 1}{' · '}{/if}
        {/each}
      </p>
    {/if}
  </div>
</footer>

<style>
  .footer {
    padding-top: 8px;
    padding-bottom: max(24px, env(safe-area-inset-bottom));
  }

  .box {
    display: grid;
    gap: 8px;
    padding: 16px 18px;
    font-size: 0.8125rem;
    color: var(--ink-soft);
  }

  .disclaimer a,
  .sources a {
    color: var(--link);
    font-weight: 600;
  }

  .sources {
    color: var(--ink-faint);
  }
</style>
