import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchCurrentUser, logout as logoutRequest } from '@/api/auth'
import type { CurrentUser } from '@/types/user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<CurrentUser | null>(null)
  const loaded = ref(false)

  const isLoggedIn = computed(() => user.value !== null)

  // 未登入或後端沒開時都視為訪客，首頁照常顯示
  async function loadCurrentUser() {
    try {
      user.value = await fetchCurrentUser()
    } catch {
      user.value = null
    } finally {
      loaded.value = true
    }
  }

  async function logout() {
    await logoutRequest()
    user.value = null
  }

  return { user, loaded, isLoggedIn, loadCurrentUser, logout }
})
