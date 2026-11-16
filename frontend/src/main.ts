import { createApp } from 'vue';
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';
import App from './App.vue';

// Temas y recursos de PrimeVue v3
import 'primevue/resources/themes/lara-light-blue/theme.css';
import 'primevue/resources/primevue.min.css';
import 'primeicons/primeicons.css';

// Tokens de diseño y estilos globales basados en DESIGN.md
import './assets/styles/tokens.css';
import './assets/styles/main.css';

const app = createApp(App);

app.use(PrimeVue, { ripple: true });
app.use(ToastService);

app.mount('#app');
