import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/user'

const ComingSoonView = () => import('@/views/ComingSoonView.vue')

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    // auth：登入註冊頁；console：老師後台與學生專區，不顯示首頁導覽列
    layout?: 'auth' | 'console'
    role?: UserRole
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/courses', name: 'courses', component: () => import('@/views/CoursesView.vue'), meta: { title: '全部課程' } },

    // ---------- 登入與註冊
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { title: '登入', layout: 'auth' },
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('@/views/auth/SignupView.vue'),
      meta: { title: '註冊', layout: 'auth' },
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('@/views/auth/ForgotPasswordView.vue'),
      meta: { title: '忘記密碼', layout: 'auth' },
    },
    {
      // 首頁課程卡的「聯繫老師」：未登入先登入，學生登入後建立對話並打開聊天
      path: '/courses/:id/contact',
      name: 'contact-teacher',
      component: () => import('@/views/student/ContactTeacherView.vue'),
      meta: { title: '聯繫老師', layout: 'auth' },
    },

    // ---------- 老師後台
    {
      path: '/teacher',
      component: () => import('@/layouts/TeacherLayout.vue'),
      meta: { layout: 'console', role: 'teacher' },
      children: [
        { path: '', name: 'teacher-home', component: () => import('@/views/teacher/TeacherDashboardView.vue'), meta: { title: '資訊總覽' } },
        { path: 'studio', name: 'teacher-studio', component: () => import('@/views/teacher/TeacherStudioView.vue'), meta: { title: '工作室管理' } },
        {
          // 設定：個人資料、基本資料、修改密碼
          path: 'settings',
          component: () => import('@/views/teacher/TeacherSettingsView.vue'),
          children: [
            { path: '', name: 'teacher-settings', redirect: '/teacher/settings/profile' },
            { path: 'profile', name: 'teacher-profile', component: () => import('@/views/teacher/TeacherProfileView.vue'), meta: { title: '個人資料' } },
            { path: 'profile/edit', name: 'teacher-profile-edit', component: () => import('@/views/teacher/TeacherProfileEditView.vue'), meta: { title: '個人資料維護' } },
            { path: 'account', name: 'teacher-account', component: () => import('@/views/teacher/TeacherAccountView.vue'), meta: { title: '基本資料' } },
            { path: 'password', name: 'teacher-password', component: () => import('@/views/teacher/TeacherPasswordView.vue'), meta: { title: '修改密碼' } },
          ],
        },
        // 舊網址導到設定裡的新位置
        { path: 'profile', redirect: '/teacher/settings/profile' },
        { path: 'profile/edit', redirect: '/teacher/settings/profile/edit' },
        { path: 'schedule', name: 'teacher-schedule', component: () => import('@/views/teacher/TeacherScheduleView.vue'), meta: { title: '課表' } },
        { path: 'students', name: 'teacher-students', component: () => import('@/views/teacher/TeacherStudentsView.vue'), meta: { title: '學生管理' } },
        { path: 'courses', name: 'teacher-courses', component: () => import('@/views/teacher/TeacherCoursesView.vue'), meta: { title: '課程管理' } },
        { path: 'courses/new', name: 'teacher-course-new', component: () => import('@/views/teacher/TeacherCourseFormView.vue'), meta: { title: '新增課程' } },
        { path: 'courses/:id/edit', name: 'teacher-course-edit', component: () => import('@/views/teacher/TeacherCourseFormView.vue'), meta: { title: '修改課程' } },
        { path: 'practice', name: 'teacher-practice', component: () => import('@/views/teacher/TeacherPracticeView.vue'), meta: { title: '作業管理' } },
        { path: 'chat', name: 'teacher-chat', component: () => import('@/views/teacher/TeacherChatListView.vue'), meta: { title: '聊天管理' } },
        { path: 'chat/:id', name: 'teacher-chat-room', component: () => import('@/views/teacher/TeacherChatRoomView.vue'), meta: { title: '聊天內容' } },
      ],
    },

    // ---------- 管理員後台
    {
      path: '/admin',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { layout: 'console', role: 'admin' },
      children: [
        { path: '', name: 'admin-home', component: () => import('@/views/admin/AdminDashboardView.vue'), meta: { title: '資訊總覽' } },
        { path: 'applications', name: 'admin-applications', component: () => import('@/views/admin/AdminApplicationsView.vue'), meta: { title: '老師申請' } },
        { path: 'teachers', name: 'admin-teachers', component: () => import('@/views/admin/AdminPeopleView.vue'), meta: { title: '老師' } },
        { path: 'students', name: 'admin-students', component: () => import('@/views/admin/AdminPeopleView.vue'), meta: { title: '學生' } },
        { path: 'password-resets', name: 'admin-password-resets', component: () => import('@/views/admin/AdminPasswordResetsView.vue'), meta: { title: '重設密碼' } },
      ],
    },

    // ---------- 學生專區
    {
      path: '/student',
      component: () => import('@/layouts/StudentLayout.vue'),
      meta: { layout: 'console', role: 'student' },
      children: [
        { path: '', name: 'student-home', component: () => import('@/views/student/StudentDashboardView.vue'), meta: { title: '我的課程' } },
        { path: 'chat/:id', name: 'student-chat-room', component: () => import('@/views/student/StudentChatRoomView.vue'), meta: { title: '聊天' } },
        { path: 'schedule', name: 'student-schedule', component: () => import('@/views/student/StudentScheduleView.vue'), meta: { title: '課表' } },
        { path: 'practice', name: 'student-practice', component: () => import('@/views/student/StudentPracticeView.vue'), meta: { title: '練習' } },
        { path: 'profile', name: 'student-profile', component: () => import('@/views/student/StudentProfileView.vue'), meta: { title: '基本資料' } },
      ],
    },

    { path: '/search', name: 'search', component: ComingSoonView, meta: { title: '搜尋課程' } },
    { path: '/courses/:id', name: 'course-detail', component: ComingSoonView, meta: { title: '課程詳情' } },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: ComingSoonView, meta: { title: '找不到頁面' } },
  ],
  scrollBehavior: (to, from, saved) => {
    if (saved) return saved
    // 其他頁點導覽列的「課程」「老師」等，回首頁後捲到該區塊
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return to.path === from.path ? undefined : { top: 0 }
  },
})

// 需要登入的頁面：沒登入先去登入頁，身分不對就回自己的首頁
router.beforeEach(async (to) => {
  const role = to.matched.find((record) => record.meta.role)?.meta.role
  if (!role) return true
  const auth = useAuthStore()
  await auth.ensureLoaded()
  if (!auth.user) return { name: 'login', query: { redirect: to.fullPath, role } }
  if (auth.user.role !== role) return auth.homePath
  return true
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title}｜melo` : 'melo｜一對一鋼琴課'
})

export default router
