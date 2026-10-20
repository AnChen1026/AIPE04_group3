<script setup lang="ts">
import { useRoute } from 'vue-router'

// 老師設定：個人資料（學生看到的介紹）、基本資料（帳號）、修改密碼。各分頁是子路由
const tabs = [
  { to: '/teacher/settings/profile', label: '個人資料' },
  { to: '/teacher/settings/account', label: '基本資料' },
  { to: '/teacher/settings/password', label: '修改密碼' },
]

// 「個人資料維護」（/settings/profile/edit）也算在個人資料分頁
const route = useRoute()
const isActive = (to: string) => route.path === to || route.path.startsWith(`${to}/`)
</script>

<template>
  <div class="settings">
    <nav class="settings__tabs" aria-label="設定項目">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.to"
        :to="tab.to"
        class="settings__tab"
        :class="{ 'settings__tab--active': isActive(tab.to) }"
        :aria-current="isActive(tab.to) ? 'page' : undefined"
      >
        {{ tab.label }}
      </RouterLink>
    </nav>
    <RouterView />
  </div>
</template>

<style scoped>
.settings__tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  padding: 4px;
  overflow-x: auto;
  border-radius: var(--radius-pill);
  background: var(--home-cream);
  width: fit-content;
  max-width: 100%;
}

.settings__tab {
  flex-shrink: 0;
  padding: 8px 18px;
  border-radius: var(--radius-pill);
  color: var(--home-muted);
  font-size: 14px;
  white-space: nowrap;
  transition: background 0.2s ease, color 0.2s ease;
}

.settings__tab:hover {
  color: var(--home-ink);
}

.settings__tab--active {
  background: var(--home-paper);
  color: var(--home-accent-dark);
  box-shadow: 0 1px 4px rgba(80, 58, 40, 0.1);
}
</style>
