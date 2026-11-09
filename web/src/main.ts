import { mount } from 'svelte';
import App from './App.svelte';
import { i18n } from './lib/i18n/i18n.svelte';
import './lib/theme.svelte'; // applies the remembered appearance
import '@fontsource-variable/sora';
import '@fontsource/barlow-semi-condensed/800-italic.css';
// Styled title of the Bluebird tile (latin only, ~13 KB, fetched when first used).
import '@fontsource/righteous/latin-400.css';
// Styled title of the avalanche tile (latin only, ~13 KB, fetched when first used).
import '@fontsource/oswald/latin-700.css';
import './styles/tokens.css';
import './styles/base.css';
import './styles/glass.css';

document.documentElement.lang = i18n.locale;

const target = document.getElementById('app');
if (!target) throw new Error('#app element missing from index.html');

export default mount(App, { target });
