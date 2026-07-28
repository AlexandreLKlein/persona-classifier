import { createRouter, createWebHistory } from 'vue-router'
import CustomerLeaderboard from '@/views/CustomerLeaderboard.vue'
import CustomerDetail from '@/views/CustomerDetail.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'leaderboard', component: CustomerLeaderboard },
    { path: '/customers/:id', name: 'customer-detail', component: CustomerDetail, props: true },
  ],
})

export default router
