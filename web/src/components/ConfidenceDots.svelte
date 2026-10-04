<!--
  Reliability of a probability as three dots: one filled for low, two for
  medium, three for high. Decorative (aria-hidden): the caller states the
  level in text or in an accessible label.
  Colours come from custom properties a parent can override:
    --dot-on   filled dot (default --prob-high)
    --dot-off  empty dot (default --track)
-->
<script lang="ts">
  import type { ConfidenceLevel } from '../lib/ranking';

  let { level, size = 6 }: { level: ConfidenceLevel; size?: number } = $props();
</script>

<span class="dots" data-level={level} style="--size: {size}px" aria-hidden="true">
  <i></i><i></i><i></i>
</span>

<style>
  .dots {
    display: inline-flex;
    gap: calc(var(--size) / 2);
    vertical-align: middle;
  }

  i {
    width: var(--size);
    height: var(--size);
    border-radius: 50%;
    background: var(--dot-off, var(--track));
  }

  [data-level='low'] i:nth-child(-n + 1),
  [data-level='medium'] i:nth-child(-n + 2),
  [data-level='high'] i {
    background: var(--dot-on, var(--prob-high));
  }
</style>
