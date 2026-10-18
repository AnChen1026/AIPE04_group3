<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

defineOptions({ name: 'HomeNavbar' })

const router = useRouter()
const authStore = useAuthStore()
const solid = ref(false)

function updateBar() {
  const hero = document.querySelector('.hero')
  if (!hero) {
    solid.value = window.scrollY > 12
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

onUnmounted(() => {
  window.removeEventListener('scroll', updateBar)
  window.removeEventListener('resize', updateBar)
})
</script>

<template>
  <header class="navbar" :class="{ 'navbar--solid': solid }">
    <div class="navbar__inner">
      <RouterLink to="/" class="navbar__brand">琴室</RouterLink>

      <nav class="navbar__links" aria-label="首頁區塊">
        <a href="#about">關於</a>
        <a href="#courses">課程</a>
        <a href="#flow">上課流程</a>
        <a href="#teachers">老師</a>
        <a href="#faq">常見問題</a>
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
  font-family: var(--font-serif);
  font-size: 26px;
  font-weight: 600;
  transition: color 0.35s ease;
  letter-spacing: 0.04em;
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
