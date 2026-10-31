<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { answerRecommendation, startRecommendation } from '@/api/recommendations'
import type { RecommendationResponse } from '@/types/recommendation'
import { deliveryText, priceText } from '@/utils/format'

interface ChatMessage { role: 'assistant' | 'user'; text: string }

const open = ref(false)
const input = ref('')
const loading = ref(false)
const error = ref('')
const response = ref<RecommendationResponse | null>(null)
const messages = ref<ChatMessage[]>([
  { role: 'assistant', text: '告訴我你想學什麼樣的鋼琴課，我會從老師已發布的課程中幫你找。' },
])
const inputElement = ref<HTMLInputElement | null>(null)

const canSubmit = computed(() => input.value.trim().length > 0 && !loading.value && response.value?.status !== 'unsupported')
const criteriaSummary = computed(() => {
  const criteria = response.value?.criteria
  if (!criteria) return []
  const labels: Record<string, string> = {
    learning_goal: '學習目標', level: '程度', style: '曲風', delivery_mode: '方式', region: '地區', max_price: '預算', time_slot: '時段',
  }
  return Object.entries(criteria)
    .filter(([, value]) => value !== null)
    .map(([key, value]) => {
      const shown = key === 'delivery_mode' ? deliveryText(String(value)) : key === 'max_price' ? `NT$ ${Number(value).toLocaleString('zh-TW')} 以下` : String(value)
      return `${labels[key] ?? key}：${shown}`
    })
})

async function toggle() {
  open.value = !open.value
  if (open.value) await nextTick(() => inputElement.value?.focus())
}

async function submit() {
  const text = input.value.trim()
  if (!text || !canSubmit.value) return
  messages.value.push({ role: 'user', text })
  input.value = ''
  error.value = ''
  loading.value = true
  try {
    const next = response.value
      ? await answerRecommendation(response.value.session_id, text)
      : await startRecommendation(text)
    response.value = next
    messages.value.push({ role: 'assistant', text: next.question ?? next.message })
  } catch (caught) {
    messages.value.pop()
    input.value = text
    error.value = caught instanceof Error ? caught.message : '系統忙碌中，請稍後再試。'
  } finally {
    loading.value = false
    await nextTick(() => inputElement.value?.focus())
  }
}

function restart() {
  response.value = null
  error.value = ''
  input.value = ''
  messages.value = [{ role: 'assistant', text: '我們重新開始。這次想找什麼樣的鋼琴課？' }]
  nextTick(() => inputElement.value?.focus())
}
</script>

<template>
  <div class="ai-assist">
    <section v-if="open" class="ai-assist__panel" role="dialog" aria-label="AI 找課助理">
      <header class="ai-assist__header">
        <div>
          <p class="ai-assist__eyebrow">只查詢正式課程資料</p>
          <h2>AI 找課助理</h2>
        </div>
        <button class="icon-button" type="button" aria-label="關閉找課助理" @click="open = false">×</button>
      </header>

      <div class="ai-assist__body" aria-live="polite">
        <div class="messages">
          <p v-for="(message, index) in messages" :key="index" class="message" :class="`message--${message.role}`">
            {{ message.text }}
          </p>
          <p v-if="loading" class="message message--assistant">正在比對課程…</p>
        </div>

        <div v-if="criteriaSummary.length" class="criteria">
          <span v-for="item in criteriaSummary" :key="item">{{ item }}</span>
        </div>

        <div v-if="response?.results.length" class="results">
          <article v-for="item in response.results" :key="item.course.id" class="course-card">
            <p class="course-card__teacher">{{ item.course.teacher_name }}</p>
            <h3>{{ item.course.title }}</h3>
            <p>{{ [item.course.level, item.course.style, deliveryText(item.course.delivery_mode)].filter(Boolean).join('・') }}</p>
            <p>{{ item.course.region || '地區未填' }}・{{ priceText(item.course.price_per_lesson) }}</p>
            <p class="course-card__reason">{{ item.reason }}</p>
            <RouterLink :to="`/courses/${item.course.id}/contact`">聯繫老師</RouterLink>
          </article>
        </div>

        <p v-if="error" class="error" role="alert">{{ error }}</p>
      </div>

      <form v-if="response?.status !== 'unsupported'" class="composer" @submit.prevent="submit">
        <label class="sr-only" for="course-request">描述找課需求</label>
        <input
          id="course-request"
          ref="inputElement"
          v-model="input"
          maxlength="1000"
          :disabled="loading"
          :placeholder="response?.status === 'done' ? '補充或修改找課條件…' : response ? '回答上面的問題…' : '例如：零基礎，想學流行鋼琴'"
        />
        <button type="submit" :disabled="!canSubmit">送出</button>
      </form>
      <button v-if="response" class="restart" type="button" @click="restart">重新找一次</button>
      <p v-if="response?.status === 'asking'" class="question-count">已追問 {{ response.questions_asked }} / 2 題</p>
    </section>

    <button type="button" class="ai-assist__button" :aria-expanded="open" @click="toggle">
      <span aria-hidden="true">✦</span> AI 找課
    </button>
  </div>
</template>

<style scoped>
.ai-assist { position: fixed; right: 24px; bottom: 24px; z-index: 30; display: flex; flex-direction: column; align-items: flex-end; gap: 12px; }
.ai-assist__button { display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; border: 1px solid var(--home-line); border-radius: var(--radius-pill); background: var(--home-paper); color: var(--home-ink); font-size: 15px; cursor: pointer; box-shadow: 0 10px 28px rgba(80, 58, 40, .16); }
.ai-assist__button span, .ai-assist__eyebrow { color: var(--home-accent); }
.ai-assist__button:hover { background: var(--home-cream); }
.ai-assist__panel { width: min(420px, calc(100vw - 32px)); max-height: min(680px, calc(100vh - 110px)); display: flex; flex-direction: column; overflow: hidden; background: var(--home-paper); border: 1px solid var(--home-line); border-radius: 22px; box-shadow: var(--shadow-soft); color: var(--home-ink); }
.ai-assist__header { display: flex; justify-content: space-between; gap: 16px; padding: 18px 20px 14px; border-bottom: 1px solid var(--home-line); }
.ai-assist__header h2 { margin: 3px 0 0; font-size: 20px; font-weight: 600; }
.ai-assist__eyebrow { margin: 0; font-size: 11px; letter-spacing: .08em; }
.icon-button { align-self: flex-start; border: 0; background: transparent; color: var(--home-muted); font-size: 25px; line-height: 1; cursor: pointer; }
.ai-assist__body { min-height: 190px; padding: 16px; overflow-y: auto; }
.messages { display: grid; gap: 9px; }
.message { width: fit-content; max-width: 88%; margin: 0; padding: 9px 12px; border-radius: 14px; font-size: 14px; line-height: 1.55; }
.message--assistant { background: var(--home-cream); border-bottom-left-radius: 4px; }
.message--user { justify-self: end; background: var(--home-ink); color: var(--home-paper); border-bottom-right-radius: 4px; }
.criteria { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 14px; }
.criteria span { padding: 4px 8px; border: 1px solid var(--home-line); border-radius: 999px; color: var(--home-muted); font-size: 12px; }
.results { display: grid; gap: 10px; margin-top: 14px; }
.course-card { padding: 14px; border: 1px solid var(--home-line); border-radius: 14px; background: #fff; }
.course-card h3, .course-card p { margin: 0 0 5px; }
.course-card h3 { font-size: 16px; }
.course-card p { color: var(--home-muted); font-size: 12px; }
.course-card__teacher { color: var(--home-accent) !important; font-weight: 600; }
.course-card__reason { margin-top: 8px !important; }
.course-card a { display: inline-block; margin-top: 7px; color: var(--home-accent); font-size: 13px; font-weight: 600; }
.composer { display: flex; gap: 8px; padding: 13px 16px; border-top: 1px solid var(--home-line); }
.composer input { min-width: 0; flex: 1; padding: 10px 12px; border: 1px solid var(--home-line); border-radius: 10px; background: #fff; color: var(--home-ink); font: inherit; }
.composer button, .restart { border: 0; border-radius: 10px; background: var(--home-ink); color: var(--home-paper); cursor: pointer; }
.composer button { padding: 0 15px; }
.composer button:disabled { cursor: default; opacity: .45; }
.restart { margin: 0 16px 14px; padding: 11px; }
.question-count { margin: -6px 16px 12px; color: var(--home-muted); font-size: 11px; text-align: right; }
.error { margin: 12px 0 0; color: #a23a2f; font-size: 13px; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
@media (max-width: 760px) { .ai-assist { right: 16px; bottom: 16px; } .ai-assist__button { padding: 10px 16px; font-size: 14px; } .ai-assist__panel { max-height: calc(100vh - 90px); } }
</style>
