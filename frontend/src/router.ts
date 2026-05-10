import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import HomeView from './views/HomeView.vue'
import ModulesView from './views/ModulesView.vue'
import SettingsView from './views/SettingsView.vue'
import AboutView from './views/AboutView.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: HomeView, meta: { title: 'Sensors' } },
  { path: '/modules', name: 'modules', component: ModulesView, meta: { title: 'Modules' } },
  { path: '/settings', name: 'settings', component: SettingsView, meta: { title: 'Settings' } },
  { path: '/about', name: 'about', component: AboutView, meta: { title: 'About' } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
