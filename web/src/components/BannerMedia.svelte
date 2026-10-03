<!--
  Visual of a banner: the tile photo when one is available (see lib/photos.ts),
  otherwise the static illustration. Fills its positioned parent. Shows the
  photo credit in the bottom-right corner unless `showCredit` is false (the
  tile then displays it elsewhere with PhotoCredit).
-->
<script lang="ts">
  import type { Photo } from '../lib/photos';
  import type { BannerScene } from '../tiles/options';
  import BannerArt from './BannerArt.svelte';
  import PhotoCredit from './PhotoCredit.svelte';

  let {
    scene,
    skyline = [],
    photo,
    showCredit = true,
  }: {
    scene: BannerScene;
    skyline?: number[];
    photo?: Photo;
    showCredit?: boolean;
  } = $props();
</script>

<div class="media">
  {#if photo}
    <img src={photo.url} alt="" loading="lazy" decoding="async" />
    {#if showCredit && photo.credit}
      <span class="corner"><PhotoCredit credit={photo.credit} /></span>
    {/if}
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

  .corner {
    position: absolute;
    right: 8px;
    bottom: 8px;
    max-width: 70%;
    display: flex;
  }
</style>
