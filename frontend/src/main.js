import { createApp } from 'vue';
import App from './App.vue';
import router from './router';

import Nora from '@primeuix/themes/nora';
import PrimeVue from 'primevue/config';
import ConfirmationService from 'primevue/confirmationservice';
import ToastService from 'primevue/toastservice';

import '@/assets/styles.scss';

const app = createApp(App);

app.use(router);
app.use(PrimeVue, {
    theme: {
        preset: Nora,
        options: {
            darkModeSelector: '.app-dark'
        }
    },
    locale: {
        noFileChosenMessage: 'Aucun fichier choisie',
        emptySearchMessage: 'Aucun resultat trouvé'
    }
});
app.use(ToastService);
app.use(ConfirmationService);

app.mount('#app');
