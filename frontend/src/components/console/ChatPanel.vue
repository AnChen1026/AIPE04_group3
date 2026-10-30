<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import type { Message } from '@/types/api'
import { formatDateTime } from '@/utils/format'

// 聊天內容：上方對象與課程，中間訊息，下方輸入框。老師與學生共用。
const props = defineProps<{
  title: string
  subtitle?: string
  messages: Message[]
  myId: string
  loading?: boolean
  error?: string
  connected?: boolean
  // 管理員對話不走即時連線，不顯示連線狀態
  hideStatus?: boolean
  // 有給的話用它判斷是不是自己這一方的訊息（管理員之間共用一段對話）
  isMine?: (message: Message) => boolean
}>()

const emit = defineEmits<{ send: [body: string] }>()
const draft = ref('')
const list = ref<HTMLElement | null>(null)

async function scrollToEnd() {
  await nextTick()
  list.value?.scrollTo({ top: list.value.scrollHeight })
}

watch(() => props.messages.length, scrollToEnd)
// 訊息下方另外放的內容（例如老師的可上課時段）出現時，外面呼叫它捲到底
defineExpose({ scrollToEnd })

function submit() {
  const text = draft.value.trim()
  if (!text) return
  emit('send', text)
  draft.value = ''
}

function onKeydown(event: KeyboardEvent) {
  // Enter 送出，Shift+Enter 換行；輸入法選字中不送出
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    submit()
  }
}
</script>

<template>
  <div class="chat">
    <header class="chat__head">
      <div>
        <strong>{{ title }}</strong>
        <span v-if="subtitle" class="chat__subtitle">{{ subtitle }}</span>
      </div>
      <span v-if="!hideStatus" class="chat__status" :class="{ 'chat__status--on': connected }">{{ connected ? '即時連線中' : '重新連線中…' }}</span>
    </header>
    <div v-if="$slots.actions" class="chat__actions"><slot name="actions" /></div>

    <div ref="list" class="chat__list" aria-live="polite">
      <p v-if="loading" class="empty">讀取訊息中…</p>
      <p v-else-if="error" class="empty">{{ error }}</p>
      <p v-else-if="messages.length === 0" class="empty">還沒有訊息，先打聲招呼吧。</p>
      <div
        v-for="message in messages"
        :key="message.id"
        class="chat__row"
        :class="{ 'chat__row--mine': isMine ? isMine(message) : message.sender_id === myId }"
      >
        <div class="chat__bubble">
          <p>{{ message.body }}</p>
          <time :datetime="message.created_at">{{ formatDateTime(message.created_at) }}</time>
        </div>
      </div>
      <slot name="after" />
    </div>

    <form class="chat__form" @submit.prevent="submit">
      <label class="visually-hidden" for="chat-input">輸入訊息</label>
      <textarea
        id="chat-input"
        v-model="draft"
        class="textarea"
        rows="1"
        placeholder="輸入訊息，Enter 送出"
        @keydown="onKeydown"
      ></textarea>
      <button type="submit" class="btn btn--primary" :disabled="!draft.trim()">送出</button>
    </form>
  </div>
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  height: min(70vh, 640px);
  border: 1px solid var(--home-line);
  border-radius: 22px;
  background: var(--home-paper);
  overflow: hidden;
}

.chat__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--home-line);
}

.chat__subtitle {
  margin-left: 10px;
  color: var(--home-muted);
  font-size: 13px;
}

.chat__status {
  color: var(--home-muted);
  font-size: 12px;
}

.chat__status--on::before {
  content: '';
  display: inline-block;
  width: 7px;
  height: 7px;
  margin-right: 6px;
  border-radius: 50%;
  background: #6f9a5b;
}

.chat__actions {
  padding: 12px 20px;
  border-bottom: 1px solid var(--home-line);
  background: var(--home-bg);
}

.chat__list {
  flex: 1;
  padding: 18px 20px;
  overflow-y: auto;
}

.chat__row {
  display: flex;
  margin-bottom: 12px;
}

.chat__row--mine {
  justify-content: flex-end;
}

.chat__bubble {
  max-width: min(72%, 520px);
  padding: 10px 14px;
  border-radius: 18px 18px 18px 6px;
  background: var(--home-cream);
}

.chat__row--mine .chat__bubble {
  border-radius: 18px 18px 6px 18px;
  background: var(--home-wood);
}

.chat__bubble p {
  margin: 0;
  color: var(--home-ink);
  font-size: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.chat__bubble time {
  display: block;
  margin-top: 4px;
  color: var(--home-muted);
  font-size: 11px;
}

.chat__form {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid var(--home-line);
}

.chat__form .textarea {
  min-height: 42px;
  max-height: 140px;
  padding: 10px 16px;
  border-radius: 22px;
}
</style>
