import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

// 除了首頁，其他頁面還沒做，先導到開發中頁面
const ComingSoonView = () => import('@/views/ComingSoonView.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/login', name: 'login', component: ComingSoonView, meta: { title: '登入' } },
    { path: '/signup', name: 'signup', component: ComingSoonView, meta: { title: '註冊' } },
    { path: '/search', name: 'search', component: ComingSoonView, meta: { title: '搜尋課程' } },
    { path: '/courses/:id', name: 'course-detail', component: ComingSoonView, meta: { title: '課程詳情' } },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: ComingSoonView, meta: { title: '找不到頁面' } },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

export default router
