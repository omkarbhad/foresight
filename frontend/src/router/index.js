import { createRouter, createWebHistory } from 'vue-router'
import SimulationCanvas from '../views/SimulationCanvas.vue'

const routes = [
  { path: '/', name: 'Canvas', component: SimulationCanvas },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
