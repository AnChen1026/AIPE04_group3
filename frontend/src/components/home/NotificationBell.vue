<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { timeAgo, useNotifications, type NotificationItem } from '@/composables/useNotifications'

// 首頁導覽列的鈴鐺：有新通知時右上角有小紅點，點開列出通知，點一則就到對應的頁面
const auth = useAuthStore()
const router = useRouter()
const { items, loading, error, newCount, isNew, load, markSeen } = useNotifications()
const open = ref(false)
const root = ref<HTMLElement | null>(null)
// 停在首頁時每分鐘重新整理一次，新的約課或訊息會亮紅點
const REFRESH_MS = 60_000
let timer = 0

async function toggle() {
  open.value = !open.value
  if (open.value) {
    await load(auth.user)
    markSeen()
  }
}

function go(item: NotificationItem) {
  open.value = false
  router.push(item.to)
}

function onDocumentClick(event: MouseEvent) {
  if (open.value && root.value && !root.value.contains(event.target as Node)) open.value = false
}

function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape') open.value = false
}

watch(
  () => auth.user?.id,
  () => load(auth.user),
)

onMounted(() => {
  load(auth.user)
  timer = window.setInterval(() => {
    if (!open.value) load(auth.user)
  }, REFRESH_MS)
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  window.clearInterval(timer)
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div ref="root" class="bell">
    <button
      type="button"
      class="bell__button"
      :aria-label="newCount ? `通知，${newCount} 則新的` : '通知'"
      :aria-expanded="open"
      aria-haspopup="dialog"
      @click="toggle"
    >
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
      </svg>
      <span v-if="newCount" class="bell__dot" aria-hidden="true"></span>
    </button>

    <Transition name="bell-panel">
      <section v-if="open" class="bell__panel" role="dialog" aria-label="通知">
        <header class="bell__head">
          <h2>通知</h2>
          <RouterLink :to="auth.homePath" class="bell__more" @click="open = false">到我的後台</RouterLink>
        </header>
        <p v-if="loading && !items.length" class="bell__empty">讀取中…</p>
        <p v-else-if="error" class="bell__empty" role="alert">{{ error }}</p>
        <p v-else-if="!items.length" class="bell__empty">目前沒有新的通知。</p>
        <ul v-else class="bell__list">
          <li v-for="item in items" :key="item.key">
            <button type="button" class="bell__item" :class="{ 'bell__item--new': isNew(item) }" @click="go(item)">
              <span class="bell__icon" aria-hidden="true">{{ item.icon }}</span>
              <span class="bell__text">
                <strong>{{ item.title }}</strong>
                <span v-if="item.detail" class="bell__detail">{{ item.detail }}</span>
                <span class="bell__time">{{ timeAgo(item.at) }}</span>
              </span>
            </button>
          </li>
        </ul>
      </section>
    </Transition>
  </div>
</template>

<style scoped>
.bell {
  position: relative;
}

.bell__button {
  position: relative;
  display: grid;
  place-items: center;
  /* 加上毛玻璃的 1px 框線共 34px，和右邊姓名／登出的膠囊一樣高 */
  width: 32px;
  height: 32px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: none;
  color: inherit;
  cursor: pointer;
}

.bell__dot {
  position: absolute;
  top: 5px;
  right: 6px;
  width: 8px;
  height: 8px;
  border: 1.5px solid #fff;
  border-radius: 50%;
  background: #d9412f;
}

.bell__panel {
  position: absolute;
  top: calc(100% + 12px);
  right: -8px;
  z-index: 30;
  display: flex;
  flex-direction: column;
  width: min(380px, calc(100vw - 32px));
  max-height: min(520px, 70vh);
  overflow: hidden;
  border: 1px solid var(--home-line);
  border-radius: 20px;
  background: var(--home-paper);
  box-shadow: 0 18px 40px rgba(62, 52, 44, 0.18);
  color: var(--home-ink);
}

.bell__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--home-line);
}

.bell__head h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.bell__more {
  color: var(--home-accent);
  font-size: 13px;
}

.bell__empty {
  margin: 0;
  padding: 28px 18px;
  color: var(--home-muted);
  font-size: 14px;
  text-align: center;
}

.bell__list {
  margin: 0;
  padding: 6px 0;
  overflow-y: auto;
  list-style: none;
}

.bell__item {
  position: relative;
  display: flex;
  gap: 12px;
  width: 100%;
  padding: 12px 18px 12px 26px;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.bell__item:hover {
  background: var(--home-cream);
}

/* 新的通知左邊有一個小藍點 */
.bell__item--new::before {
  position: absolute;
  top: 22px;
  left: 10px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3d7be0;
  content: '';
}

.bell__icon {
  flex: none;
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--home-cream);
  font-size: 18px;
}

.bell__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.bell__text strong {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
}

.bell__detail {
  overflow: hidden;
  color: var(--home-ink);
  font-size: 13px;
  opacity: 0.8;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bell__time {
  color: var(--home-muted);
  font-size: 12px;
}

.bell-panel-enter-active,
.bell-panel-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.bell-panel-enter-from,
.bell-panel-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
