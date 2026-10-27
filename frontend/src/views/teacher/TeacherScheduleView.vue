<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import CalendarPager, { type CalendarMode } from '@/components/console/CalendarPager.vue'
import DayStrip from '@/components/console/DayStrip.vue'
import WeekTimetable from '@/components/console/WeekTimetable.vue'
import MonthCalendar from '@/components/console/MonthCalendar.vue'
import type { TimetableItem } from '@/components/console/timetable'
import ModalPanel from '@/components/console/ModalPanel.vue'
import { decideChangeRequest, fetchChangeRequests, fetchLessonSummary, fetchMyLessons } from '@/api/teacher'
import type { LessonSummary, TeacherChangeRequest, TeacherLesson } from '@/types/api'
import { CHANGE_TYPE_LABELS, addDays, formatDateTime, formatRange, formatTime, sameDay, startOfWeek, toneClass } from '@/utils/format'

const route = useRoute()
const router = useRouter()

// 右上方切換日／週／月；anchor 是目前看的那一天（週、月就看它所在的那週、那個月）
const mode = ref<CalendarMode>('week')
const anchor = ref(new Date())
const weekStart = computed(() => startOfWeek(anchor.value))
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

// 「日」：設計稿的上方選一天，下面列出那天的課
const weekLessonDates = computed(() =>
  lessons.value
    .map((lesson) => new Date(lesson.starts_at))
    .filter((date) => date >= weekStart.value && date < addDays(weekStart.value, 7)),
)
const dayLessons = computed(() =>
  lessons.value
    .filter((lesson) => sameDay(new Date(lesson.starts_at), anchor.value))
    .sort((a, b) => a.starts_at.localeCompare(b.starts_at)),
)
const courseKeys = computed(() => [...new Set(lessons.value.map((lesson) => lesson.course_id))])

// 「共 N 堂課，已上 M 堂」：同一位學生同一門課、沒取消的課
function progress(lesson: TeacherLesson) {
  const same = lessons.value.filter(
    (item) => item.course_id === lesson.course_id && item.student_id === lesson.student_id && item.status === 'scheduled',
  )
  const done = same.filter((item) => new Date(item.ends_at) < new Date()).length
  return `共 ${same.length} 堂課，已上 ${done} 堂`
}

// 月曆上點日期：換到那天的「日」
function showDay(date: Date) {
  anchor.value = date
  mode.value = 'day'
}

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
  anchor.value = new Date(lesson.starts_at)
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
    <CalendarPager v-model="anchor" v-model:mode="mode" />
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <WeekTimetable v-if="mode === 'week'" :week-start="weekStart" :items="items" @select="openLesson" />
  <MonthCalendar v-else-if="mode === 'month'" :month="anchor" :items="items" @select="openLesson" @day="showDay" />
  <template v-else>
  <DayStrip v-model="anchor" :week-start="weekStart" :marked="weekLessonDates" />

  <div v-if="dayLessons.length === 0" class="card empty">這天沒有排課。</div>
  <article
    v-for="lesson in dayLessons"
    :key="lesson.id"
    class="tone-card lesson-card"
    :class="toneClass(lesson.course_id, courseKeys)"
  >
    <div class="tone-card__cell lesson-card__time">
      <p class="tone-card__title">{{ formatTime(lesson.starts_at) }} - {{ formatTime(lesson.ends_at) }}</p>
      <RouterLink :to="{ name: 'teacher-practice', query: { course: lesson.course_id } }" class="tone-card__line lesson-card__link">
        查看作業分析
      </RouterLink>
    </div>
    <div class="tone-card__cell">
      <p class="tone-card__title">{{ lesson.course_title }}　{{ lesson.student_name }}</p>
      <button v-if="lesson.status === 'scheduled'" type="button" class="tone-card__line lesson-card__link" @click="openLesson(lesson.id)">
        進度：看課前摘要
      </button>
    </div>
    <div class="tone-card__cell">
      <p class="tone-card__line">{{ progress(lesson) }}</p>
    </div>
    <span class="tone-btn lesson-card__status">{{ lesson.status === 'cancelled' ? '已取消' : '已確認' }}</span>
  </article>
  </template>

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
.lesson-card {
  position: relative;
  grid-template-columns: 170px minmax(0, 1.4fr) minmax(0, 1fr);
  padding-right: 110px;
}

.lesson-card__time {
  text-align: center;
}

.lesson-card__link {
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.lesson-card__link:hover {
  text-decoration: underline;
}

.lesson-card__status {
  position: absolute;
  top: 12px;
  right: 14px;
  min-height: 26px;
  padding: 0 10px;
  font-size: 13px;
  cursor: default;
}

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

@media (max-width: 720px) {
  .lesson-card {
    padding-right: 20px;
  }

  .lesson-card__time {
    text-align: left;
  }

  .lesson-card__status {
    position: static;
    justify-self: start;
  }
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
