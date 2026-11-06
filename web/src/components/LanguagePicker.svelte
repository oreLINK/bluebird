<!--
  Language popup, opened from the flag button at the top right of the header
  (components/ChoicePopup.svelte): each language with its flag and its name in
  the language itself; choosing one switches the site. The default language
  follows the browser (detectLocale in lib/i18n/core.ts) until the visitor
  picks one, which is then remembered.
-->
<script lang="ts">
  import { LOCALES, LOCALE_FLAGS, LOCALE_NAMES, type Locale } from '../lib/i18n/core';
  import { i18n } from '../lib/i18n/i18n.svelte';
  import ChoicePopup from './ChoicePopup.svelte';
  import Flag from './Flag.svelte';

  let { open, onclose }: { open: boolean; onclose: () => void } = $props();

  const options = LOCALES.map((locale) => ({ id: locale, label: LOCALE_NAMES[locale], lang: locale }));
</script>

<ChoicePopup
  {open}
  {onclose}
  id="language"
  title={i18n.t('language.title')}
  titleIcon="globe"
  closeLabel={i18n.t('language.close')}
  {options}
  current={i18n.locale}
  onchoose={(locale: Locale) => i18n.setLocale(locale)}
>
  {#snippet lead(locale: Locale)}
    <Flag country={LOCALE_FLAGS[locale]} width={30} />
  {/snippet}
</ChoicePopup>
