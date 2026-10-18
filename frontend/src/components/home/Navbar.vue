<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

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

      <nav class="navbar__actions" aria-label="帳號">
        <template v-if="authStore.isLoggedIn">
          <span class="navbar__name">{{ authStore.user?.name }}</span>
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
  transition: background 0.25s ease, border-color 0.25s ease;
}

.navbar--solid {
  background: rgba(251, 246, 239, 0.94);
  border-bottom: 1px solid var(--home-line);
  backdrop-filter: blur(10px);
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
  font-size: 28px;
  font-weight: 600;
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

@media (max-width: 640px) {
  .navbar__inner {
    padding-inline: 16px;
  }

  .navbar__brand {
    font-size: 24px;
  }
}
</style>
