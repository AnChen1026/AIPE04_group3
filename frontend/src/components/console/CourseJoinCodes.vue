<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { createJoinCode, deleteJoinCode, fetchJoinCode, issueBindingCode } from '@/api/teacher'
import type { Conversation, Course, CourseJoinCode } from '@/types/api'
import { formatDateTime } from '@/utils/format'

// 課程卡上的綁定碼：
// 1. 限時綁定碼：整門課一組，期限內拿到的學生都能加入（例如貼在團體課群組）
// 2. 洽詢中的學生：一人一碼，只給那位學生
const props = defineProps<{ course: Course; inquiries: Conversation[] }>()
const emit = defineEmits<{ changed: [] }>()

const HOURS = [
  { value: 1, label: '1 小時' },
  { value: 24, label: '24 小時' },
  { value: 72, label: '3 天' },
  { value: 168, label: '7 天' },
]

const joinCode = ref<CourseJoinCode | null>(null)
const hours = ref(24)
const busy = ref('')
const copied = ref('')
const error = ref('')

async function run(key: string, action: () => Promise<unknown>) {
  busy.value = key
  error.value = ''
  try {
    await action()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '沒有成功，請稍後再試。'
  } finally {
    busy.value = ''
  }
}

const makeJoinCode = () =>
  run('join', async () => {
    joinCode.value = await createJoinCode(props.course.id, hours.value)
  })

const stopJoinCode = () =>
  run('join', async () => {
    await deleteJoinCode(props.course.id)
    joinCode.value = null
  })

// 一人一碼也會貼進和那位學生的聊天
const issueFor = (conversation: Conversation) =>
  run(conversation.id, async () => {
    await issueBindingCode(conversation.id)
    emit('changed')
  })

async function copy(code: string) {
  await navigator.clipboard?.writeText(code).catch(() => undefined)
  copied.value = code
  window.setTimeout(() => (copied.value = ''), 1600)
}

onMounted(async () => {
  joinCode.value = await fetchJoinCode(props.course.id).catch(() => null)
})
</script>

<template>
  <section class="codes">
    <div class="codes__row">
      <span class="codes__label">限時綁定碼</span>
      <template v-if="joinCode">
        <code class="codes__code">{{ joinCode.code }}</code>
        <span class="muted">到 {{ formatDateTime(joinCode.expires_at) }} 前有效</span>
        <span class="codes__actions">
          <button type="button" class="btn btn--ghost btn--small" @click="copy(joinCode.code)">
            {{ copied === joinCode.code ? '已複製' : '複製' }}
          </button>
          <button type="button" class="btn btn--ghost btn--small" :disabled="busy === 'join'" @click="makeJoinCode">重發</button>
          <button type="button" class="btn btn--ghost btn--small" :disabled="busy === 'join'" @click="stopJoinCode">停用</button>
        </span>
      </template>
      <template v-else>
        <span class="muted">期限內拿到碼的學生都能加入這門課</span>
        <span class="codes__actions">
          <label class="visually-hidden" :for="`join-hours-${course.id}`">有效時間</label>
          <select :id="`join-hours-${course.id}`" v-model.number="hours" class="select codes__select">
            <option v-for="item in HOURS" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
          <button type="button" class="btn btn--primary btn--small" :disabled="busy === 'join'" @click="makeJoinCode">
            {{ busy === 'join' ? '產生中…' : '產生綁定碼' }}
          </button>
        </span>
      </template>
    </div>

    <div v-for="item in inquiries" :key="item.id" class="codes__row">
      <span class="codes__label">洽詢中：{{ item.student_name }}</span>
      <template v-if="item.binding_code">
        <code class="codes__code">{{ item.binding_code }}</code>
        <span class="muted">只給這位學生</span>
      </template>
      <span v-else class="muted">還沒發碼</span>
      <span class="codes__actions">
        <button v-if="item.binding_code" type="button" class="btn btn--ghost btn--small" @click="copy(item.binding_code)">
          {{ copied === item.binding_code ? '已複製' : '複製' }}
        </button>
        <button type="button" class="btn btn--ghost btn--small" :disabled="busy === item.id" @click="issueFor(item)">
          {{ item.binding_code ? '重發' : '發綁定碼' }}
        </button>
        <RouterLink :to="`/teacher/chat/${item.id}`" class="btn btn--ghost btn--small">聊天</RouterLink>
      </span>
    </div>
    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
  </section>
</template>

<style scoped>
.codes {
  margin-top: 14px;
  padding-top: 10px;
  border-top: 1px solid var(--home-line);
  font-size: 14px;
}

.codes__row {
  display: flex;
  align-items: center;
  gap: 6px 12px;
  flex-wrap: wrap;
  padding: 6px 0;
}

.codes__label {
  min-width: 96px;
  color: var(--home-ink);
  font-weight: 500;
}

.codes__code {
  padding: 2px 10px;
  border-radius: 8px;
  background: var(--home-cream);
  color: var(--home-accent-dark);
  font-size: 15px;
  letter-spacing: 0.12em;
}

.codes__actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.codes__select {
  width: auto;
  min-height: 32px;
  padding-top: 0;
  padding-bottom: 0;
  font-size: 13px;
}
</style>
