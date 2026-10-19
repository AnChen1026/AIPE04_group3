<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ConsoleIcon from './ConsoleIcon.vue'
import { useAuthStore } from '@/stores/auth'

export interface NavItem {
  to: string
  label: string
  icon: string
  badge?: number
  exact?: boolean
}

// 老師後台與學生專區共用的外框：上方標題列、左側選單、右側內容卡
defineProps<{
  heading: string
  items: NavItem[]
}>()

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const menuOpen = ref(false)

watch(
  () => route.fullPath,
  () => {
    menuOpen.value = false
  },
)

function isActive(item: NavItem) {
  return item.exact ? route.path === item.to : route.path === item.to || route.path.startsWith(item.to + '/')
}

async function logout() {
  await auth.logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <div class="shell">
    <div class="shell__frame">
      <header class="shell__top">
        <button
          type="button"
          class="shell__menu-button"
          :aria-expanded="menuOpen"
          aria-controls="shell-nav"
          @click="menuOpen = !menuOpen"
        >
          <span class="visually-hidden">選單</span>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">
            <path d="M4 7h16M4 12h16M4 17h16" />
          </svg>
        </button>
        <RouterLink to="/" class="shell__brand">琴室</RouterLink>
        <span class="shell__heading">{{ heading }}</span>
        <span class="shell__user">{{ auth.user?.name }}</span>
      </header>

      <div class="shell__body">
        <nav id="shell-nav" class="shell__nav" :class="{ 'shell__nav--open': menuOpen }" :aria-label="heading">
          <RouterLink
            v-for="item in items"
            :key="item.to"
            :to="item.to"
            class="shell__link"
            :class="{ 'shell__link--active': isActive(item) }"
            :aria-current="isActive(item) ? 'page' : undefined"
          >
            <ConsoleIcon :name="item.icon" />
            <span>{{ item.label }}</span>
            <span v-if="item.badge" class="shell__badge">{{ item.badge }}</span>
          </RouterLink>
          <button type="button" class="shell__link" @click="logout">
            <ConsoleIcon name="logout" />
            <span>登出</span>
          </button>
        </nav>

        <section class="shell__content">
          <slot />
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  padding: clamp(12px, 3vw, 36px);
  background: var(--home-cream);
}

.shell__frame {
  max-width: 1320px;
  min-height: calc(100vh - clamp(24px, 6vw, 72px));
  margin: 0 auto;
  border-radius: 32px;
  background: var(--home-bg);
  box-shadow: var(--shadow-soft);
}

.shell__top {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px clamp(20px, 3vw, 36px);
  border-bottom: 1px solid var(--home-line);
}

.shell__brand {
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: 26px;
  font-weight: 600;
  letter-spacing: 0.06em;
}

.shell__heading {
  padding-left: 16px;
  border-left: 1px solid var(--home-wood);
  color: var(--home-accent);
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 600;
}

.shell__user {
  margin-left: auto;
  color: var(--home-muted);
  font-size: 14px;
}

.shell__menu-button {
  display: none;
  padding: 6px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--home-ink);
  cursor: pointer;
}

.shell__body {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: clamp(16px, 2vw, 32px);
  padding: 24px clamp(16px, 3vw, 36px) 36px;
}

.shell__nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.shell__link {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 11px 18px;
  border: 0;
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--home-ink);
  font: inherit;
  font-size: 15px;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s ease;
}

.shell__link:hover {
  background: var(--home-cream);
}

.shell__link--active {
  background: var(--home-wood);
  font-weight: 500;
}

.shell__link svg {
  flex: none;
  color: var(--home-accent);
}

.shell__badge {
  min-width: 20px;
  margin-left: auto;
  padding: 0 6px;
  border-radius: var(--radius-pill);
  background: var(--home-accent);
  color: var(--home-paper);
  font-size: 12px;
  text-align: center;
}

.shell__content {
  min-width: 0;
}

@media (max-width: 860px) {
  .shell {
    padding: 0;
  }

  .shell__frame {
    min-height: 100vh;
    border-radius: 0;
  }

  .shell__menu-button {
    display: inline-flex;
  }

  .shell__heading {
    font-size: 16px;
  }

  .shell__user {
    display: none;
  }

  .shell__body {
    grid-template-columns: 1fr;
    padding-top: 12px;
  }

  .shell__nav {
    display: none;
    padding: 8px;
    border: 1px solid var(--home-line);
    border-radius: 20px;
    background: var(--home-paper);
  }

  .shell__nav--open {
    display: flex;
  }
}
</style>
