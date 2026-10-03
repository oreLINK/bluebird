import { mount } from 'svelte';
import App from './App.svelte';
import { i18n } from './lib/i18n/i18n.svelte';
import './styles/tokens.css';
import './styles/base.css';
import './styles/glass.css';

document.documentElement.lang = i18n.locale;

const target = document.getElementById('app');
if (!target) throw new Error('#app element missing from index.html');

export default mount(App, { target });
