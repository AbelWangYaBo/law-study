import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Reader from './views/Reader.vue'
import Recite from './views/Recite.vue'
import Dictionary from './views/Dictionary.vue'
import GraphView from './views/GraphView.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'reader', component: Reader },
    { path: '/recite', name: 'recite', component: Recite },
    { path: '/dictionary', name: 'dictionary', component: Dictionary },
    { path: '/graph', name: 'graph', component: GraphView },
  ],
})

createApp(App).use(router).mount('#app')
