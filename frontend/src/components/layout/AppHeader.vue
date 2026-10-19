<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const keyword = ref('')

function submitSearch() {
  const q = keyword.value.trim()
  if (!q) return
  router.push({ name: 'search', query: { q } })
}

async function handleLogout() {
  await authStore.logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <header class="app-header">
    <div class="container app-header__inner">
      <RouterLink to="/" class="app-header__brand">鋼琴課程管理與推廣平台</RouterLink>

      <form class="app-header__search" role="search" @submit.prevent="submitSearch">
        <label for="header-search" class="visually-hidden">搜尋課程</label>
        <input id="header-search" v-model="keyword" type="search" placeholder="搜尋課程、老師" />
        <button type="submit" aria-label="搜尋">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
        </button>
      </form>

      <div class="app-header__account">
        <template v-if="authStore.isLoggedIn">
          <span class="app-header__user">{{ authStore.user?.name }}</span>
          <button type="button" class="app-header__link" @click="handleLogout">登出</button>
        </template>
        <RouterLink v-else to="/login" class="app-header__link">登入/註冊</RouterLink>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.app-header__inner {
  display: flex;
  align-items: center;
  gap: 24px;
  min-height: var(--header-height);
}

.app-header__brand {
  font-size: 30px;
  font-weight: 700;
  white-space: nowrap;
}

.app-header__search {
  display: flex;
  align-items: center;
  width: 280px;
  height: 36px;
  margin-left: auto;
  padding: 0 6px 0 18px;
  background: var(--color-search-bg);
  border-radius: var(--radius-pill);
}

.app-header__search input {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  outline: none;
}

.app-header__search:focus-within {
  outline: 2px solid var(--color-text);
  outline-offset: 2px;
}

.app-header__search button {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.app-header__account {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: 40px;
  font-size: 20px;
  white-space: nowrap;
}

.app-header__link {
  border: 0;
  background: transparent;
  cursor: pointer;
  padding: 0;
}

.app-header__link:hover {
  text-decoration: underline;
}

@media (max-width: 760px) {
  .app-header__inner {
    flex-wrap: wrap;
    gap: 8px 16px;
    padding-top: 12px;
    padding-bottom: 12px;
  }

  .app-header__brand {
    font-size: 20px;
  }

  .app-header__account {
    margin-left: auto;
    font-size: 16px;
  }

  .app-header__search {
    order: 3;
    width: 100%;
    margin-left: 0;
  }
}
</style>
