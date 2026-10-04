<!--
  Site footer (config/pages.yaml `footer`), two short centred lines:
    1. the GitHub logo, linking to the project repository;
    2. small links to the pages (about, legal notice, privacy), each opening
       a full-window sheet (InfoPage) through `#<page id>`.
  Long texts (method, disclaimer, sources) live in those pages.
-->
<script lang="ts">
  import { footer, footerLinks } from '../lib/config';
  import type { ServiceStatus as Status } from '../lib/data';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { sheets } from '../lib/sheets.svelte';
  import Icon from './Icon.svelte';
  import { STATE_ICON, statusView } from '../lib/status';

  /** The page showing diamond/status.json (config/pages.yaml): its link carries the state. */
  const STATUS_PAGE = 'status';

  let { status, massifId, now }: { status: Status | null; massifId: string; now: number } =
    $props();

  const state = $derived(status ? statusView(status, massifId, now).state : 'down');

  function openPage(event: MouseEvent, id: string) {
    if (event.metaKey || event.ctrlKey || event.shiftKey) return; // new tab or window
    event.preventDefault();
    sheets.open(id);
  }
</script>

<footer class="container footer">
  <a
    class="github"
    href={footer.repository}
    target="_blank"
    rel="noopener noreferrer"
    aria-label={i18n.t('footer.github')}
  >
    <Icon name="github" size={26} />
  </a>
  {#if footerLinks.length}
    <nav aria-label={i18n.t('footer.pages')}>
      <ul>
        {#each footerLinks as page (page.id)}
          <li>
            <a href="#{page.id}" onclick={(event) => openPage(event, page.id)}>
              {#if page.id === STATUS_PAGE}
                <span class="state" data-state={state}><Icon name={STATE_ICON[state]} size={10} /></span
                ><span class="visually-hidden">{i18n.t(`state.${state}`)} · </span>
              {/if}{i18n.pick(page.title)}
            </a>
          </li>
        {/each}
      </ul>
    </nav>
  {/if}
</footer>

<style>
  .state {
    display: inline-grid;
    place-items: center;
    width: 14px;
    height: 14px;
    margin-right: 4px;
    border-radius: 50%;
    vertical-align: -2px;
  }

  .state[data-state='ok'] {
    background: var(--state-ok-bg);
    color: var(--state-ok-ink);
  }

  .state[data-state='partial'] {
    background: var(--state-partial-bg);
    color: var(--state-partial-ink);
  }

  .state[data-state='stale'] {
    background: var(--state-stale-bg);
    color: var(--state-stale-ink);
  }

  .state[data-state='down'] {
    background: var(--state-down-bg);
    color: var(--state-down-ink);
  }

  .footer {
    display: grid;
    justify-items: center;
    gap: 6px;
    padding-top: 12px;
    padding-bottom: max(24px, env(safe-area-inset-bottom));
  }

  .github {
    display: grid;
    place-items: center;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    color: var(--ink-soft);
  }

  ul {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0 4px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  /* The dot ends the line it is on, so a wrapped line never starts with one. */
  li:not(:last-child)::after {
    content: '·';
    margin-left: 4px;
    color: var(--ink-faint);
  }

  nav a {
    display: inline-block;
    padding: 6px 2px;
    font-size: 0.75rem;
    color: var(--ink-faint);
    text-decoration: none;
  }

  nav a:hover {
    text-decoration: underline;
  }
</style>
