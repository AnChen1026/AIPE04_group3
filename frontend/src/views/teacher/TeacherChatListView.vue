<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchTeacherConversations } from '@/api/teacher'
import { fetchSupportConversation } from '@/api/support'
import type { Conversation, SupportConversation } from '@/types/api'
import { formatShort } from '@/utils/format'

const conversations = ref<Conversation[]>([])
// 和平台管理員的對話，固定在列表最上方
const support = ref<SupportConversation | null>(null)
const keyword = ref('')
const error = ref('')
let timer = 0

const shown = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  if (!text) return conversations.value
  return conversations.value.filter((item) =>
    [item.student_name ?? '', item.course_title ?? ''].some((value) => value.toLowerCase().includes(text)),
  )
})

async function load() {
  try {
    ;[conversations.value, support.value] = await Promise.all([fetchTeacherConversations(), fetchSupportConversation().catch(() => null)])
    error.value = ''
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到聊天列表。'
  }
  timer = window.setTimeout(load, 15000)
}

onMounted(load)
onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <PageHeader title="聊天管理" description="學生在課程按「洽詢」後會出現在這裡。決定收學生時，在對話裡發綁定碼。">
    <label class="search-input">
      <span class="visually-hidden">搜尋學生</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋學生" />
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
    </label>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <RouterLink
    v-if="support"
    to="/teacher/support"
    class="card conversation conversation--admin"
    :class="{ 'conversation--unread': support.unread_count > 0 }"
  >
    <span class="conversation__avatar" aria-hidden="true">管</span>
    <div class="conversation__main">
      <div class="conversation__title">
        <strong>平台管理員</strong>
        <span class="badge badge--soft">置頂</span>
      </div>
      <p class="muted">通知與使用協助</p>
      <p v-if="support.last_message" class="conversation__last">{{ support.last_message }}</p>
    </div>
    <div class="conversation__side">
      <span class="muted">{{ formatShort(support.last_message_at) }}</span>
      <span v-if="support.unread_count" class="conversation__unread">未讀訊息 {{ support.unread_count }} 則</span>
    </div>
  </RouterLink>

  <p class="muted list__caption">近期聊天紀錄</p>
  <div v-if="shown.length === 0" class="card empty">
    {{ conversations.length === 0 ? '還沒有學生洽詢。' : '找不到符合的學生。' }}
  </div>
  <RouterLink
    v-for="item in shown"
    :key="item.id"
    :to="`/teacher/chat/${item.id}`"
    class="card conversation"
    :class="{ 'conversation--unread': item.unread_count > 0 }"
  >
    <span class="conversation__avatar" aria-hidden="true">{{ (item.student_name ?? '學').slice(0, 1) }}</span>
    <div class="conversation__main">
      <div class="conversation__title">
        <strong>學生：{{ item.student_name }}</strong>
        <span class="badge" :class="item.bound ? 'badge--accent' : 'badge--muted'">{{ item.bound ? '已綁定' : '洽詢中' }}</span>
      </div>
      <p class="muted">{{ item.course_title }}{{ item.course_level ? `・${item.course_level}` : '' }}</p>
      <p v-if="item.last_message" class="conversation__last">{{ item.last_message }}</p>
    </div>
    <div class="conversation__side">
      <span class="muted">{{ formatShort(item.last_message_at) }}</span>
      <span v-if="item.unread_count" class="conversation__unread">未讀訊息 {{ item.unread_count }} 則</span>
    </div>
  </RouterLink>
</template>

<style scoped>
.search-input {
  width: min(220px, 100%);
}

.list__caption {
  margin: 0 0 10px;
  font-size: 14px;
}

.conversation {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 22px;
  transition: border-color 0.2s ease;
}

.conversation:hover {
  border-color: var(--home-wood);
}

.conversation + .conversation {
  margin-top: 12px;
}

.conversation--admin {
  margin-bottom: 22px;
  border-color: var(--home-wood);
}

.conversation--unread {
  background: var(--home-cream);
}

.conversation__avatar {
  display: grid;
  place-items: center;
  flex: none;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: var(--home-wood);
  color: var(--home-accent-dark);
  font-family: var(--font-serif);
  font-size: 18px;
}

.conversation__main {
  flex: 1;
  min-width: 0;
}

.conversation__title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.conversation__main p {
  margin: 2px 0 0;
  font-size: 13px;
}

.conversation__last {
  overflow: hidden;
  color: var(--home-ink);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation__side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  font-size: 12px;
}

.conversation__unread {
  color: var(--home-accent-dark);
  font-size: 14px;
  font-weight: 500;
}
</style>
