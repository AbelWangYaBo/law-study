import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import Reader from './views/Reader.vue'
import Recite from './views/Recite.vue'
import Dictionary from './views/Dictionary.vue'
import GraphView from './views/GraphView.vue'
import InspectView from './views/InspectView.vue'
import './style.css'

const router = createRouter({
  history: createWebHashHistory(),  // hash 路由：GitHub Pages 子路径下刷新无需服务器兜底
  routes: [
    { path: '/', name: 'reader', component: Reader },
    { path: '/recite', name: 'recite', component: Recite },
    { path: '/dictionary', name: 'dictionary', component: Dictionary },
    { path: '/graph', name: 'graph', component: GraphView },
    { path: '/inspect', name: 'inspect', component: InspectView },
  ],
})

createApp(App).use(router).mount('#app')
