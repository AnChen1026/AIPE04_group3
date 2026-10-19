<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import WeekPicker from '@/components/console/WeekPicker.vue'
import WeekTimetable, { type TimetableItem } from '@/components/console/WeekTimetable.vue'
import ModalPanel from '@/components/console/ModalPanel.vue'
import { decideChangeRequest, fetchChangeRequests, fetchLessonSummary, fetchMyLessons } from '@/api/teacher'
import type { LessonSummary, TeacherChangeRequest, TeacherLesson } from '@/types/api'
import { CHANGE_TYPE_LABELS, formatDateTime, formatRange, startOfWeek } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const weekStart = ref(startOfWeek(new Date()))
const lessons = ref<TeacherLesson[]>([])
const requests = ref<TeacherChangeRequest[]>([])
const error = ref('')
const deciding = ref('')
const requestError = ref('')

const selected = ref<TeacherLesson | null>(null)
const summary = ref<LessonSummary | null>(null)
const summaryLoading = ref(false)
const summaryError = ref('')

const items = computed<TimetableItem[]>(() =>
  lessons.value.map((lesson) => ({
    id: lesson.id,
    starts_at: lesson.starts_at,
    ends_at: lesson.ends_at,
    title: lesson.course_title,
    subtitle: lesson.student_name,
    colorKey: lesson.course_id,
    cancelled: lesson.status === 'cancelled',
  })),
)

async function load() {
  error.value = ''
  try {
    ;[lessons.value, requests.value] = await Promise.all([fetchMyLessons(), fetchChangeRequests()])
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到課表。'
  }
}

async function openLesson(id: string) {
  const lesson = lessons.value.find((item) => item.id === id)
  if (!lesson) return
  selected.value = lesson
  weekStart.value = startOfWeek(new Date(lesson.starts_at))
  summary.value = null
  summaryError.value = ''
  if (lesson.status !== 'scheduled') return
  summaryLoading.value = true
  try {
    summary.value = await fetchLessonSummary(id)
  } catch (problem) {
    summaryError.value = problem instanceof Error ? problem.message : '讀不到課前摘要。'
  } finally {
    summaryLoading.value = false
  }
}

function closeLesson() {
  selected.value = null
  if (route.query.summary) router.replace({ query: {} })
}

async function decide(item: TeacherChangeRequest, approve: boolean) {
  deciding.value = item.id
  requestError.value = ''
  try {
    await decideChangeRequest(item.id, approve)
  } catch (problem) {
    // 時段被占用時後端會直接拒絕這筆申請，正式課表不變
    requestError.value = problem instanceof Error ? problem.message : '處理失敗，請稍後再試。'
  } finally {
    deciding.value = ''
    await load()
  }
}

function proposed(item: TeacherChangeRequest) {
  return item.proposed_starts_at && item.proposed_ends_at ? formatRange(item.proposed_starts_at, item.proposed_ends_at) : ''
}

function original(item: TeacherChangeRequest) {
  return item.session_starts_at && item.session_ends_at ? formatRange(item.session_starts_at, item.session_ends_at) : ''
}

onMounted(async () => {
  await load()
  if (typeof route.query.summary === 'string') openLesson(route.query.summary)
})

watch(
  () => route.query.summary,
  (id) => {
    if (typeof id === 'string') openLesson(id)
  },
)
</script>

<template>
  <PageHeader title="課表" description="點一堂課可以看課前摘要。學生的約課、請假、調課要在這裡確認後才會改動課表。">
    <WeekPicker v-model="weekStart" />
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <WeekTimetable :week-start="weekStart" :items="items" @select="openLesson" />

  <section class="card requests">
    <h2 class="card__title">待確認的課務申請</h2>
    <p v-if="requestError" class="error-text" role="alert">{{ requestError }}</p>
    <p v-if="requests.length === 0" class="muted">目前沒有待確認的申請。</p>
    <ul>
      <li v-for="item in requests" :key="item.id" class="request">
        <div class="request__main">
          <span class="badge badge--soft">{{ CHANGE_TYPE_LABELS[item.request_type] }}</span>
          <strong>{{ item.student_name }}</strong>
          <span class="muted">{{ item.course_title }}</span>
        </div>
        <dl class="request__detail">
          <template v-if="original(item)">
            <dt>原本</dt>
            <dd>{{ original(item) }}</dd>
          </template>
          <template v-if="proposed(item)">
            <dt>{{ item.request_type === 'booking' ? '想約' : '改到' }}</dt>
            <dd>{{ proposed(item) }}</dd>
          </template>
          <template v-if="item.reason">
            <dt>原因</dt>
            <dd>{{ item.reason }}</dd>
          </template>
          <dt>送出</dt>
          <dd>{{ formatDateTime(item.created_at) }}</dd>
        </dl>
        <div class="request__actions">
          <button type="button" class="btn btn--ghost btn--small" :disabled="deciding === item.id" @click="decide(item, false)">不同意</button>
          <button type="button" class="btn btn--primary btn--small" :disabled="deciding === item.id" @click="decide(item, true)">同意</button>
        </div>
      </li>
    </ul>
  </section>

  <ModalPanel :open="selected !== null" :title="selected ? `${selected.course_title}｜${selected.student_name}` : ''" wide @close="closeLesson">
    <template v-if="selected">
      <p class="lesson__time">
        {{ formatRange(selected.starts_at, selected.ends_at) }}
        <span v-if="selected.status === 'cancelled'" class="badge badge--muted">已取消</span>
      </p>
      <h3 class="lesson__heading">課前摘要</h3>
      <p v-if="selected.status === 'cancelled'" class="muted">這堂課已取消，沒有課前摘要。</p>
      <p v-else-if="summaryLoading" class="muted">整理這段期間的練習中…</p>
      <p v-else-if="summaryError" class="error-text">{{ summaryError }}</p>
      <template v-else-if="summary">
        <p class="muted lesson__range">
          範圍：{{ summary.window_start ? formatDateTime(summary.window_start) : '開始上課以來' }} ～ {{ formatDateTime(summary.window_end) }}
        </p>
        <div class="lesson__stats">
          <span>練習 <strong>{{ summary.stats.recording_count }}</strong> 次</span>
          <span>完成 <strong>{{ summary.stats.completed_count }}</strong></span>
          <span>失敗 <strong>{{ summary.stats.failed_count }}</strong></span>
          <span>分析中 <strong>{{ summary.stats.waiting_count }}</strong></span>
          <span v-if="summary.stats.average_pitch_score !== undefined">平均音高 <strong>{{ summary.stats.average_pitch_score }}</strong></span>
          <span v-if="summary.stats.average_rhythm_score !== undefined">平均節奏 <strong>{{ summary.stats.average_rhythm_score }}</strong></span>
        </div>
        <p class="lesson__summary">{{ summary.summary_text }}</p>
        <p class="lesson__meta">
          {{ summary.written_by === 'llm' ? 'AI 撰寫' : '依統計自動產生' }}・{{ formatDateTime(summary.generated_at) }}
        </p>
      </template>
    </template>
  </ModalPanel>
</template>

<style scoped>
.requests {
  margin-top: 18px;
}

.requests ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.request {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px 16px;
  padding: 14px 0;
  border-top: 1px solid var(--home-line);
}

.request:first-child {
  border-top: 0;
}

.request__main {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.request__detail {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 2px 12px;
  margin: 0;
  font-size: 14px;
}

.request__detail dt {
  color: var(--home-muted);
}

.request__detail dd {
  margin: 0;
}

.request__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  grid-row: 1 / span 2;
  grid-column: 2;
}

.lesson__time {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
}

.lesson__heading {
  margin: 18px 0 6px;
  font-size: 16px;
  font-weight: 500;
}

.lesson__range {
  margin: 0;
  font-size: 13px;
}

.lesson__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
}

.lesson__stats span {
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  background: var(--home-cream);
  font-size: 13px;
}

.lesson__summary {
  margin: 0;
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--home-bg);
  line-height: 1.8;
  white-space: pre-wrap;
}

.lesson__meta {
  margin: 8px 0 0;
  color: var(--home-muted);
  font-size: 12px;
}

@media (max-width: 640px) {
  .request {
    grid-template-columns: 1fr;
  }

  .request__actions {
    grid-row: auto;
    grid-column: auto;
  }
}
</style>
