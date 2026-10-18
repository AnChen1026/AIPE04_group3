import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchCurrentUser, login as loginRequest, logout as logoutRequest } from '@/api/auth'
import type { CurrentUser } from '@/types/user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<CurrentUser | null>(null)
  const loaded = ref(false)
  let loading: Promise<void> | null = null

  const isLoggedIn = computed(() => user.value !== null)

  // 登入後該去的地方：管理員、老師、學生各自進自己的後台
  const homePath = computed(() => {
    if (user.value?.role === 'admin') return '/admin'
    if (user.value?.role === 'teacher') return '/teacher'
    if (user.value?.role === 'student') return '/student'
    return '/'
  })

  // 未登入或後端沒開時都視為訪客，首頁照常顯示
  function loadCurrentUser(): Promise<void> {
    loading ??= fetchCurrentUser()
      .then((current) => {
        user.value = current
      })
      .catch(() => {
        user.value = null
      })
      .finally(() => {
        loaded.value = true
      })
    return loading
  }

  async function ensureLoaded() {
    if (!loaded.value) await loadCurrentUser()
  }

  async function login(email: string, password: string) {
    user.value = await loginRequest(email, password)
    loaded.value = true
    return user.value
  }

  async function logout() {
    await logoutRequest().catch(() => undefined)
    user.value = null
  }

  return { user, loaded, isLoggedIn, homePath, loadCurrentUser, ensureLoaded, login, logout }
})
