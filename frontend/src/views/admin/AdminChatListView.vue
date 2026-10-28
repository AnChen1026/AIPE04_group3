<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import ChatSplit from '@/components/console/ChatSplit.vue'
import { fetchAdminConversations } from '@/api/support'
import type { SupportConversation } from '@/types/api'
import { formatShort } from '@/utils/format'

// 管理員和所有老師、學生的對話。每個人預設都在列表上，沒聊過的也能直接開口；
// 老師審核通過、學生註冊時系統已經先送出第一則。
// 左邊是列表，右邊直接顯示選到的對話（子路由 chat/:id）
const route = useRoute()
const conversations = ref<SupportConversation[]>([])
const keyword = ref('')
const role = ref<'' | 'teacher' | 'student'>('')
const error = ref('')
let timer = 0

const ROLE_LABELS: Record<string, string> = { teacher: '老師', student: '學生' }

const shown = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return conversations.value.filter(
    (item) => (!role.value || item.user_role === role.value) && (!text || item.user_name.toLowerCase().includes(text)),
  )
})

async function load() {
  window.clearTimeout(timer)
  try {
    conversations.value = await fetchAdminConversations()
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
  <PageHeader title="聊天" description="所有老師、學生都在這裡，可以直接開始對話。老師審核通過、學生註冊成功時，系統會先送出歡迎與使用須知。">
    <label class="search-input">
      <span class="visually-hidden">搜尋姓名</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋姓名" />
    </label>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <ChatSplit :has-room="Boolean(route.params.id)" back-to="/admin/chat">
    <div class="chip-group list__filters" role="group" aria-label="依身分篩選">
      <button type="button" class="chip" :aria-pressed="role === ''" @click="role = ''">全部</button>
      <button type="button" class="chip" :aria-pressed="role === 'teacher'" @click="role = 'teacher'">老師</button>
      <button type="button" class="chip" :aria-pressed="role === 'student'" @click="role = 'student'">學生</button>
    </div>

    <div v-if="shown.length === 0" class="card empty">
      {{ conversations.length === 0 ? '還沒有任何老師或學生。' : '找不到符合的人。' }}
    </div>
    <RouterLink
      v-for="item in shown"
      :key="item.id"
      :to="`/admin/chat/${item.id}`"
      class="chat-item"
      active-class="chat-item--active"
      :class="{ 'chat-item--unread': item.unread_count > 0 }"
    >
      <span class="chat-item__avatar" aria-hidden="true">{{ item.user_name.slice(0, 1) }}</span>
      <div class="chat-item__main">
        <div class="chat-item__title">
          <strong>{{ item.user_name }}</strong>
          <span class="badge badge--soft">{{ ROLE_LABELS[item.user_role] ?? item.user_role }}</span>
          <time>{{ formatShort(item.last_message_at) }}</time>
        </div>
        <p v-if="item.last_message" class="chat-item__line chat-item__line--last">{{ item.last_message }}</p>
        <p v-else class="chat-item__line">還沒有訊息，點開就能開始聊。</p>
      </div>
      <span v-if="item.unread_count" class="chat-item__unread" :aria-label="`未讀 ${item.unread_count} 則`">{{ item.unread_count }}</span>
    </RouterLink>
  </ChatSplit>
</template>

<style scoped>
.search-input {
  width: min(220px, 100%);
}

.list__filters {
  margin-bottom: 12px;
}
</style>
