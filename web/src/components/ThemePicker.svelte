<!--
  Appearance popup, opened from the button left of the language button
  (components/ChoicePopup.svelte): System (default, follows the device),
  Light or Dark, each with its icon (lib/theme.ts). The choice is applied at
  once and remembered on the device.
-->
<script lang="ts">
  import { i18n } from '../lib/i18n/i18n.svelte';
  import { THEMES, THEME_ICONS, type ThemeChoice } from '../lib/theme';
  import { theme } from '../lib/theme.svelte';
  import ChoicePopup from './ChoicePopup.svelte';
  import Icon from './Icon.svelte';

  let { open, onclose }: { open: boolean; onclose: () => void } = $props();

  const LABELS = { system: 'theme.system', light: 'theme.light', dark: 'theme.dark' } as const;
  const options = $derived(THEMES.map((t) => ({ id: t, label: i18n.t(LABELS[t]) })));
</script>

<ChoicePopup
  {open}
  {onclose}
  id="theme"
  title={i18n.t('theme.title')}
  titleIcon={THEME_ICONS[theme.choice]}
  closeLabel={i18n.t('theme.close')}
  {options}
  current={theme.choice}
  onchoose={(choice: ThemeChoice) => theme.set(choice)}
>
  {#snippet lead(choice: ThemeChoice)}
    <span class="lead"><Icon name={THEME_ICONS[choice]} size={22} /></span>
  {/snippet}
</ChoicePopup>

<style>
  .lead {
    display: grid;
    place-items: center;
    width: 30px;
  }
</style>
