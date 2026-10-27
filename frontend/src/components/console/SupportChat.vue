<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import ChatPanel from './ChatPanel.vue'
import { useAuthStore } from '@/stores/auth'
import type { Message } from '@/types/api'

// 平台管理員對話的聊天畫面：老師、學生、管理員共用。沒有即時連線，每 5 秒重新讀一次訊息
const props = defineProps<{
  title: string
  subtitle?: string
  load: () => Promise<Message[]>
  send: (body: string, clientMessageId: string) => Promise<Message>
  // 管理員看的時候給對話的使用者 id：不是他發的就算管理員這一方
  ownerId?: string
}>()

const auth = useAuthStore()
const messages = ref<Message[]>([])
const loading = ref(true)
const error = ref('')
let timer = 0

async function refresh() {
  window.clearTimeout(timer)
  try {
    messages.value = await props.load()
    error.value = ''
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到這段對話。'
  } finally {
    loading.value = false
  }
  timer = window.setTimeout(refresh, 5000)
}

async function onSend(body: string) {
  try {
    const message = await props.send(body, crypto.randomUUID())
    if (!messages.value.some((item) => item.id === message.id)) messages.value.push(message)
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '訊息沒有送出。'
  }
}

onMounted(refresh)
onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <ChatPanel
    :title="title"
    :subtitle="subtitle"
    :messages="messages"
    :my-id="auth.user?.id ?? ''"
    :loading="loading"
    :error="error"
    hide-status
    :is-mine="ownerId ? (message) => message.sender_id !== ownerId : undefined"
    @send="onSend"
  />
</template>
