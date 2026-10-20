<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

defineOptions({ name: 'HomeNavbar' })

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const solid = ref(false)

function updateBar() {
  const hero = document.querySelector('.hero')
  // 沒有大圖的頁面（例如全部課程）一律用米色底，否則白字會看不到
  if (!hero) {
    solid.value = true
    return
  }
  // 大圖還鋪滿畫面時，導覽列維持透明；大圖離開後才補上米色底
  solid.value = hero.getBoundingClientRect().bottom < 80
}

async function handleLogout() {
  await authStore.logout()
  router.push({ name: 'home' })
}

onMounted(() => {
  updateBar()
  window.addEventListener('scroll', updateBar, { passive: true })
  window.addEventListener('resize', updateBar)
})

// 導覽列只掛一次，換頁後重新判斷有沒有大圖
watch(
  () => route.path,
  async () => {
    await nextTick()
    updateBar()
  },
)

onUnmounted(() => {
  window.removeEventListener('scroll', updateBar)
  window.removeEventListener('resize', updateBar)
})
</script>

<template>
  <header class="navbar" :class="{ 'navbar--solid': solid }">
    <div class="navbar__inner">
      <RouterLink to="/" class="navbar__brand" aria-label="melo">melo.</RouterLink>

      <nav class="navbar__links" aria-label="首頁區塊">
        <RouterLink :to="{ path: '/', hash: '#about' }">關於</RouterLink>
        <RouterLink :to="{ path: '/', hash: '#courses' }">課程</RouterLink>
        <RouterLink :to="{ path: '/', hash: '#flow' }">上課流程</RouterLink>
        <RouterLink :to="{ path: '/', hash: '#teachers' }">老師</RouterLink>
        <RouterLink :to="{ path: '/', hash: '#faq' }">常見問題</RouterLink>
      </nav>

      <nav class="navbar__actions" aria-label="帳號">
        <template v-if="authStore.isLoggedIn">
          <RouterLink :to="authStore.homePath" class="navbar__name">{{ authStore.user?.name }}</RouterLink>
          <button type="button" class="navbar__text" @click="handleLogout">登出</button>
        </template>
        <template v-else>
          <RouterLink to="/login" class="navbar__text">Login</RouterLink>
          <RouterLink to="/signup" class="navbar__signup">Sign up</RouterLink>
        </template>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  right: 0;
  left: 0;
  z-index: 20;
  background: transparent;
  border-bottom: 1px solid transparent;
  transition: background 0.35s ease, border-color 0.35s ease;
}

.navbar--solid {
  background: rgba(251, 246, 239, 0.94);
  border-bottom: 1px solid var(--home-line);
  backdrop-filter: blur(10px);
}

/* 還在大圖上時，文字用米白色，和大圖上的標題一致 */
.navbar:not(.navbar--solid) .navbar__brand,
.navbar:not(.navbar--solid) .navbar__links,
.navbar:not(.navbar--solid) .navbar__name,
.navbar:not(.navbar--solid) .navbar__text {
  color: var(--home-paper);
  text-shadow: 0 1px 12px rgba(52, 42, 34, 0.25);
}

.navbar__links {
  display: flex;
  gap: 28px;
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

.navbar__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: var(--header-height);
  padding: 0 clamp(20px, 4vw, 48px);
}

.navbar__brand {
  color: var(--home-ink);
  font-family: var(--font-logo);
  font-size: 28px;
  font-weight: 400;
  line-height: 1;
  letter-spacing: 0.01em;
  transition: color 0.35s ease;
}

.navbar__actions {
  display: flex;
  align-items: center;
  gap: 18px;
}

.navbar__name,
.navbar__text {
  color: var(--home-ink);
  font-size: 15px;
}

.navbar__text {
  border: 0;
  background: transparent;
  padding: 0;
  cursor: pointer;
}

.navbar__signup {
  padding: 8px 16px;
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
    font-size: 24px;
  }
}
</style>
