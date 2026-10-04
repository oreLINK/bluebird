<!--
  Visual of a banner: the tile photo when one is available (see lib/photos.ts),
  otherwise the static illustration. Fills its positioned parent. The photo
  credit is not shown here: it is on the back of the tile (KpiBack) and on
  the legal notice page.
-->
<script lang="ts">
  import type { Photo } from '../lib/photos';
  import type { BannerScene } from '../tiles/options';
  import BannerArt from './BannerArt.svelte';

  let {
    scene,
    skyline = [],
    photo,
  }: {
    scene: BannerScene;
    skyline?: number[];
    photo?: Photo;
  } = $props();
</script>

<div class="media">
  {#if photo}
    <img src={photo.url} alt="" loading="lazy" decoding="async" />
  {:else}
    <BannerArt {scene} {skyline} />
  {/if}
</div>

<style>
  .media {
    position: absolute;
    inset: 0;
  }

  img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
</style>
