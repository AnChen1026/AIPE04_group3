<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NotificationBell from './NotificationBell.vue'

defineOptions({ name: 'HomeNavbar' })

const router = useRouter()
const authStore = useAuthStore()

async function handleLogout() {
  await authStore.logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <header class="navbar">
    <div class="navbar__inner">
      <RouterLink to="/" class="navbar__brand navbar__glass" aria-label="melo">melo.</RouterLink>

      <nav class="navbar__links navbar__glass" aria-label="首頁區塊">
        <RouterLink :to="{ path: '/', hash: '#about' }">關於</RouterLink>
        <RouterLink :to="{ path: '/', hash: '#courses' }">課程</RouterLink>
        <RouterLink :to="{ path: '/', hash: '#flow' }">上課流程</RouterLink>
        <RouterLink :to="{ path: '/', hash: '#teachers' }">老師</RouterLink>
        <RouterLink :to="{ path: '/', hash: '#faq' }">常見問題</RouterLink>
      </nav>

      <nav class="navbar__actions" aria-label="帳號">
        <template v-if="authStore.isLoggedIn">
          <NotificationBell v-if="authStore.user?.role !== 'admin'" class="navbar__glass navbar__bell" />
          <RouterLink :to="authStore.homePath" class="navbar__name navbar__pill navbar__glass">{{ authStore.user?.name }}</RouterLink>
          <button type="button" class="navbar__text navbar__pill navbar__glass" @click="handleLogout">登出</button>
        </template>
        <div v-else class="navbar__account navbar__glass">
          <RouterLink to="/login" class="navbar__text">Login</RouterLink>
          <RouterLink to="/signup" class="navbar__signup">Sign up</RouterLink>
        </div>
      </nav>
    </div>
  </header>
</template>

<style scoped>
/* 整列透明；只有 logo、選單、鈴鐺、帳號這幾塊各自是半透明毛玻璃的膠囊（UIUX 回饋） */
.navbar {
  position: fixed;
  top: 0;
  right: 0;
  left: 0;
  z-index: 20;
  background: transparent;
  pointer-events: none;
}

.navbar__inner > *,
.navbar__actions > * {
  pointer-events: auto;
}

.navbar__glass {
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: var(--radius-pill);
  background: rgba(251, 246, 239, 0.45);
  box-shadow: 0 6px 20px rgba(62, 52, 44, 0.1);
  -webkit-backdrop-filter: blur(14px) saturate(1.3);
  backdrop-filter: blur(14px) saturate(1.3);
}

.navbar__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  min-height: var(--header-height);
  padding: 0 clamp(20px, 4vw, 48px);
}

.navbar__brand {
  padding: 6px 20px 8px;
  color: var(--home-ink);
  font-family: var(--font-logo);
  font-size: 28px;
  font-weight: 400;
  line-height: 1;
  letter-spacing: 0.01em;
}

.navbar__links {
  display: flex;
  gap: 28px;
  padding: 9px 28px;
  color: var(--home-ink);
  font-size: 15px;
}

.navbar__links a {
  opacity: 0.86;
  transition: opacity 0.2s ease;
}

.navbar__links a:hover {
  opacity: 1;
}

.navbar__actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.navbar__bell {
  color: var(--home-ink);
}

.navbar__account {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 4px 4px 4px 18px;
}

.navbar__name,
.navbar__text {
  color: var(--home-ink);
  font-size: 15px;
}

.navbar__text {
  cursor: pointer;
}

/* 未登入時 Login 是膠囊裡的純文字；登入後的「登出」自己是一顆毛玻璃膠囊 */
.navbar__text:not(.navbar__glass) {
  border: 0;
  background: transparent;
  padding: 0;
}

/* 登入後姓名、登出各自一顆膠囊，高度和鈴鐺一樣 34px */
.navbar__pill {
  display: inline-flex;
  align-items: center;
  height: 34px;
  padding: 0 16px;
  font: inherit;
  font-size: 15px;
}

/* Sign up 用主色的實心膠囊，和 Login 區分開 */
.navbar__signup {
  padding: 7px 16px;
  border-radius: var(--radius-pill);
  background: var(--home-accent);
  color: var(--home-paper);
  font-size: 15px;
}

.navbar__text:hover,
.navbar__signup:hover {
  opacity: 0.82;
}

@media (max-width: 900px) {
  .navbar__links {
    display: none;
  }
}

@media (max-width: 640px) {
  .navbar__inner {
    padding-inline: 16px;
  }

  .navbar__brand {
    padding: 5px 14px 7px;
    font-size: 24px;
  }

  .navbar__account {
    gap: 10px;
    padding-left: 14px;
  }
}
</style>
