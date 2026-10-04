<!--
  Bluebird wordmark: text only, no mark. Two-tone italic display type, "bird"
  with a light-blue gradient and a short underline swoosh. (The favicon,
  web/public/favicon.svg, keeps the former mountain mark.)
-->
<script lang="ts">
  /** Wordmark height scale: 1 is the header size. */
  let { scale = 1 }: { scale?: number } = $props();
</script>

<span class="wordmark" style="--scale: {scale}"><span class="a">Blue</span><span class="b">bird</span></span>

<style>
  .wordmark {
    display: inline-block;
    font-family: var(--font-display);
    font-size: calc(2.375rem * var(--scale, 1));
    font-style: italic;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.025em;
    /* Room for the italic overhang of the last letter. */
    padding-right: 0.08em;
  }

  .a {
    color: var(--logo-a);
  }

  .b {
    position: relative;
    color: var(--logo-b);
    background: linear-gradient(100deg, var(--logo-b) 20%, var(--sky));
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .b::after {
    content: '';
    position: absolute;
    left: 0.06em;
    right: 0.02em;
    bottom: -0.1em;
    height: 0.1em;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--logo-b), var(--sky));
    transform: skewX(-18deg);
  }

  @media (forced-colors: active) {
    .b {
      -webkit-text-fill-color: currentColor;
    }
  }
</style>
