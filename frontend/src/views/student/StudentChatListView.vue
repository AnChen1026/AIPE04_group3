<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import ChatSplit from '@/components/console/ChatSplit.vue'
import { fetchMyConversations } from '@/api/student'
import { fetchSupportConversation } from '@/api/support'
import type { Conversation, SupportConversation } from '@/types/api'
import { formatShort } from '@/utils/format'

// 左邊是對話列表，右邊直接顯示選到的對話（子路由 chat/:id、chat/admin）
const route = useRoute()
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
    [item.teacher_name ?? '', item.course_title ?? ''].some((value) => value.toLowerCase().includes(text)),
  )
})

async function load() {
  window.clearTimeout(timer)
  try {
    ;[conversations.value, support.value] = await Promise.all([fetchMyConversations(), fetchSupportConversation().catch(() => null)])
    error.value = ''
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到聊天列表。'
  }
  timer = window.setTimeout(load, 15000)
}

// 打開一段對話後，那段的未讀數會歸零，稍等一下再更新列表
watch(
  () => route.params.id,
  () => window.setTimeout(load, 800),
)

onMounted(load)
onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <PageHeader title="聊天記錄" description="在課程按「聯繫老師」後，和老師的對話都在這裡。">
    <label class="search-input">
      <span class="visually-hidden">搜尋老師</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋老師" />
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
    </label>
    <RouterLink :to="{ path: '/', hash: '#courses' }" class="btn btn--primary">新增</RouterLink>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <ChatSplit :has-room="Boolean(route.params.id) || route.name === 'student-support'" back-to="/student/chat">
    <RouterLink
      v-if="support"
      to="/student/chat/admin"
      class="chat-item chat-item--pinned"
      active-class="chat-item--active"
      :class="{ 'chat-item--unread': support.unread_count > 0 }"
    >
      <span class="chat-item__avatar" aria-hidden="true">管</span>
      <div class="chat-item__main">
        <div class="chat-item__title">
          <strong>平台管理員</strong>
          <span class="badge badge--soft">置頂</span>
          <time>{{ formatShort(support.last_message_at) }}</time>
        </div>
        <p class="chat-item__line chat-item__line--last">{{ support.last_message || '通知與使用協助' }}</p>
      </div>
      <span v-if="support.unread_count" class="chat-item__unread" :aria-label="`未讀 ${support.unread_count} 則`">{{ support.unread_count }}</span>
    </RouterLink>

    <p class="chat-list__caption">近期聊天紀錄</p>
    <div v-if="shown.length === 0" class="card empty">
      {{ conversations.length === 0 ? '還沒有和老師聊過。按右上角「新增」到首頁找課程、聯繫老師。' : '找不到符合的老師。' }}
    </div>
    <RouterLink
      v-for="item in shown"
      :key="item.id"
      :to="`/student/chat/${item.id}`"
      class="chat-item"
      active-class="chat-item--active"
      :class="{ 'chat-item--unread': item.unread_count > 0 }"
    >
      <span class="chat-item__avatar" aria-hidden="true">{{ (item.teacher_name ?? '師').slice(0, 1) }}</span>
      <div class="chat-item__main">
        <div class="chat-item__title">
          <strong>{{ item.teacher_name }} 老師</strong>
          <span class="badge" :class="item.bound ? 'badge--accent' : 'badge--muted'">{{ item.bound ? '上課中' : '洽詢中' }}</span>
          <time>{{ formatShort(item.last_message_at) }}</time>
        </div>
        <p class="chat-item__line">{{ item.course_title }}{{ item.course_level ? `・${item.course_level}` : '' }}</p>
        <p v-if="item.last_message" class="chat-item__line chat-item__line--last">{{ item.last_message }}</p>
      </div>
      <span v-if="item.unread_count" class="chat-item__unread" :aria-label="`未讀 ${item.unread_count} 則`">{{ item.unread_count }}</span>
    </RouterLink>
  </ChatSplit>
</template>

<style scoped>
.search-input {
  width: min(220px, 100%);
}
</style>
