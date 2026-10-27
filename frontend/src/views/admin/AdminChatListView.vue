<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchAdminConversations } from '@/api/support'
import type { SupportConversation } from '@/types/api'
import { formatShort } from '@/utils/format'

// 管理員和所有老師、學生的對話。老師審核通過、學生註冊時系統已經先送出第一則
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

onMounted(load)
onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <PageHeader title="聊天" description="和老師、學生的對話。老師審核通過、學生註冊成功時，系統會先送出歡迎與使用須知。">
    <label class="search-input">
      <span class="visually-hidden">搜尋姓名</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋姓名" />
    </label>
  </PageHeader>
  <div class="chip-group list__filters" role="group" aria-label="依身分篩選">
    <button type="button" class="chip" :aria-pressed="role === ''" @click="role = ''">全部</button>
    <button type="button" class="chip" :aria-pressed="role === 'teacher'" @click="role = 'teacher'">老師</button>
    <button type="button" class="chip" :aria-pressed="role === 'student'" @click="role = 'student'">學生</button>
  </div>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="shown.length === 0" class="card empty">
    {{ conversations.length === 0 ? '還沒有任何對話。' : '找不到符合的對話。' }}
  </div>
  <RouterLink
    v-for="item in shown"
    :key="item.id"
    :to="`/admin/chat/${item.id}`"
    class="card conversation"
    :class="{ 'conversation--unread': item.unread_count > 0 }"
  >
    <span class="conversation__avatar" aria-hidden="true">{{ item.user_name.slice(0, 1) }}</span>
    <div class="conversation__main">
      <div class="conversation__title">
        <strong>{{ item.user_name }}</strong>
        <span class="badge badge--soft">{{ ROLE_LABELS[item.user_role] ?? item.user_role }}</span>
      </div>
      <p v-if="item.last_message" class="conversation__last">{{ item.last_message }}</p>
    </div>
    <div class="conversation__side">
      <span class="muted">{{ formatShort(item.last_message_at) }}</span>
      <span v-if="item.unread_count" class="conversation__unread">未讀 {{ item.unread_count }} 則</span>
    </div>
  </RouterLink>
</template>

<style scoped>
.search-input {
  width: min(220px, 100%);
}

.list__filters {
  margin-bottom: 16px;
}

.conversation {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 22px;
}

.conversation + .conversation {
  margin-top: 12px;
}

.conversation:hover {
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

.conversation__last {
  margin: 4px 0 0;
  overflow: hidden;
  font-size: 13px;
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
