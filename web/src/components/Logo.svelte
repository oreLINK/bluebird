<!--
  Bluebird logo: a mark (two snowy peaks under a deep-blue sky, with a
  bluebird in flight) and a two-tone italic wordmark. Also used as favicon
  (web/public/favicon.svg keeps the same mark).
-->
<script lang="ts">
  let { size = 34 }: { size?: number } = $props();
</script>

<span class="logo">
  <svg class="mark" width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
    <defs>
      <linearGradient id="bb-logo-sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#0b2a5b" />
        <stop offset="1" stop-color="#1f6fd1" />
      </linearGradient>
    </defs>
    <rect width="40" height="40" rx="11" fill="url(#bb-logo-sky)" />
    <path d="M22 11.5c1.6-1.9 3.4-1.9 5 0 1.6-1.9 3.4-1.9 5 0" fill="none" stroke="#7cc4ff"
      stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
    <path d="M3 34 14.5 17.5l5.5 7.5 5-6.5L37 34Z" fill="#ffffff" />
    <path d="M14.5 17.5 11 22.6l2.6-1.2 1.6 1.6 1.7-1.9Z M25 18.5l-2.3 3 2.3-.9 1.8 1.4 1.1-.9Z"
      fill="#cfe5fa" />
  </svg>
  <span class="wordmark"><span class="a">Blue</span><span class="b">bird</span></span>
</span>

<style>
  .logo {
    display: inline-flex;
    align-items: center;
    gap: 9px;
  }

  .mark {
    flex: none;
  }

  .wordmark {
    font-family: var(--font-display);
    font-size: 1.75rem;
    font-style: italic;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.01em;
  }

  .a {
    color: var(--logo-a);
  }

  .b {
    color: var(--logo-b);
  }
</style>
