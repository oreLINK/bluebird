<!--
  A page of config/pages.yaml shown in a full-window Sheet: one section per
  entry, with its paragraphs, its links and its built-in block:
    data_sources   attribution of every enabled source (config/sources.yaml)
    photo_credits  credit of every banner photo (assets/photos/credits.yaml)
  Open while `#<page id>` is in the URL (lib/sheets.svelte.ts).
-->
<script lang="ts">
  import { attributions, stationNames, type Page } from '../lib/config';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { photoCredits } from '../lib/photos';
  import { sheets } from '../lib/sheets.svelte';
  import Sheet from './Sheet.svelte';

  let { page }: { page: Page } = $props();

  /** `pyrenees/cauterets/cauterets_1` → the station name, else the file name. */
  const photoLabel = (key: string) =>
    stationNames.get(key.split('/').slice(0, 2).join('/')) ?? key.split('/').at(-1) ?? key;
</script>

<Sheet
  id={page.id}
  title={i18n.pick(page.title)}
  open={sheets.current === page.id}
  onclose={() => sheets.close()}
>
  {#each page.sections as section (section.id)}
    <section aria-labelledby="{page.id}-{section.id}">
      <h3 id="{page.id}-{section.id}">{i18n.pick(section.title)}</h3>
      {#each section.paragraphs ?? [] as paragraph, index (index)}
        <p>{i18n.pick(paragraph)}</p>
      {/each}

      {#if section.block === 'data_sources'}
        <ul>
          {#each attributions as source (source.name + source.url)}
            <li>
              <a href={source.url} target="_blank" rel="noopener noreferrer">{source.name}</a>
              {#if source.license}<span class="muted">({source.license})</span>{/if}
            </li>
          {/each}
        </ul>
      {:else if section.block === 'photo_credits'}
        {#if photoCredits.length}
          <ul>
            {#each photoCredits as { key, credit } (key)}
              <li>
                <span>{photoLabel(key)}</span> ·
                {#if credit.url}
                  <a href={credit.url} target="_blank" rel="noopener noreferrer">{credit.author}</a>
                {:else}
                  {credit.author}
                {/if}
                {#if credit.license}<span class="muted">({credit.license})</span>{/if}
              </li>
            {/each}
          </ul>
        {:else}
          <p class="muted">{i18n.t('page.noPhotos')}</p>
        {/if}
      {/if}

      {#if section.links?.length}
        <ul class="links">
          {#each section.links as link (link.url)}
            <li>
              <a href={link.url} target="_blank" rel="noopener noreferrer">{i18n.pick(link.label)}</a>
            </li>
          {/each}
        </ul>
      {/if}
    </section>
  {/each}
</Sheet>

<style>
  section {
    display: grid;
    gap: 8px;
    padding: 18px 0;
    border-bottom: 1px solid var(--glass-border);
  }

  section:last-child {
    border-bottom: 0;
  }

  h3 {
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }

  p,
  li {
    font-size: 0.9375rem;
    line-height: 1.55;
    color: var(--ink);
  }

  ul {
    display: grid;
    gap: 4px;
    margin: 0;
    padding-left: 18px;
  }

  .links {
    list-style: none;
    padding: 0;
  }

  a {
    color: var(--link);
    font-weight: 650;
  }

  .muted {
    color: var(--ink-soft);
  }
</style>
