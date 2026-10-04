<!--
  Site footer: the service status of the last refresh (ServiceStatus), then
  (config/pages.yaml `footer`) two short centred lines:
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
  import ServiceStatus from './ServiceStatus.svelte';

  let {
    status,
    massifId,
    timezone,
    now,
  }: { status: Status | null; massifId: string; timezone: string; now: number } = $props();

  function openPage(event: MouseEvent, id: string) {
    if (event.metaKey || event.ctrlKey || event.shiftKey) return; // new tab or window
    event.preventDefault();
    sheets.open(id);
  }
</script>

<footer class="container footer">
  <div class="service-box">
    <ServiceStatus {status} {massifId} {timezone} {now} />
  </div>
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
              {i18n.pick(page.title)}
            </a>
          </li>
        {/each}
      </ul>
    </nav>
  {/if}
</footer>

<style>
  .service-box {
    justify-self: stretch;
    margin-bottom: 6px;
    font-size: 0.8125rem;
    color: var(--ink-soft);
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

  li + li::before {
    content: '·';
    margin-right: 4px;
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
