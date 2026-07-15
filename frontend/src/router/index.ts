import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
    { path: '/board', name: 'board', component: () => import('@/views/BoardListView.vue') },
    { path: '/posts/new', name: 'post-create', component: () => import('@/views/PostFormView.vue') },
    { path: '/posts/:id', name: 'post-detail', component: () => import('@/views/PostDetailView.vue') },
    { path: '/posts/:id/edit', name: 'post-edit', component: () => import('@/views/PostFormView.vue') },
    { path: '/locations', name: 'locations', component: () => import('@/views/LocationsView.vue') },
    { path: '/dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
    { path: '/locations/:contentid', name: 'location-detail', component: () => import('@/views/LocationDetailView.vue') },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue') },
  ],
})

export default router
