import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';

import App from './App.vue';
import Home from './pages/Home.vue';
import Transcribe from './pages/Transcribe.vue';
import Translate from './pages/Translate.vue';
import Models from './pages/Models.vue';

const routes = [
    { path: '/', component: Home },
    { path: '/transcribe', component: Transcribe },
    { path: '/translate', component: Translate },
    { path: '/models', component: Models },
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

const app = createApp(App)
app.use(router)
app.mount('#app')