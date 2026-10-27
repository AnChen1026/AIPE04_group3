<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import FeedbackView from '@/components/console/FeedbackView.vue'
import ModalPanel from '@/components/console/ModalPanel.vue'
import { fetchCourseRecordings, fetchMyCourses, fetchMyStudents } from '@/api/teacher'
import { apiUrl } from '@/api/http'
import type { BoundStudent, Course, TeacherRecording } from '@/types/api'
import { RECORDING_STATUS_LABELS, formatDateTime, toneClass } from '@/utils/format'

// 設計稿的「作業狀態」：每位學生在每門課的演奏作業（照參考 MIDI 錄的練習）有沒有繳交，點「查看詳情」看每次錄音與回饋。
// 題庫作業與繳交期限後端還沒有，先留位置
const route = useRoute()
const courses = ref<Course[]>([])
const students = ref<BoundStudent[]>([])
const recordings = ref<TeacherRecording[]>([])
const keyword = ref('')
const filter = ref<'all' | 'submitted' | 'missing'>('all')
const error = ref('')
const detailKey = ref('')
const addOpen = ref(false)
let timer = 0

const filters = [
  { value: 'all', label: '全部' },
  { value: 'submitted', label: '已繳交' },
  { value: 'missing', label: '未繳交' },
] as const

interface HomeworkRow {
  key: string
  course: Course
  studentId: string
  studentName: string
  recordings: TeacherRecording[]
}

// 一位學生 × 一門課 = 一張卡；網址帶 ?course= 時只看那門課（從課表的「查看作業分析」進來）
const rows = computed<HomeworkRow[]>(() => {
  const onlyCourse = typeof route.query.course === 'string' ? route.query.course : ''
  const list: HomeworkRow[] = []
  for (const student of students.value) {
    for (const bound of student.courses) {
      const course = courses.value.find((item) => item.id === bound.course_id)
      if (!course || (onlyCourse && course.id !== onlyCourse)) continue
      list.push({
        key: `${course.id}:${student.id}`,
        course,
        studentId: student.id,
        studentName: student.name,
        recordings: recordings.value.filter((item) => item.course_id === course.id && item.student_id === student.id),
      })
    }
  }
  return list
})

const shown = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return rows.value.filter(
    (row) =>
      (filter.value === 'all' || (filter.value === 'submitted') === row.recordings.length > 0) &&
      (!text || [row.studentName, row.course.title].some((value) => value.toLowerCase().includes(text))),
  )
})

const courseKeys = computed(() => courses.value.map((item) => item.id))
const detail = computed(() => rows.value.find((row) => row.key === detailKey.value) ?? null)

function statusText(row: HomeworkRow) {
  if (!row.course.has_reference_midi) return '作業待上傳'
  return row.recordings.length ? '作業已上傳，學生已繳交' : '作業已上傳，學生未繳交'
}

function lastText(row: HomeworkRow) {
  const latest = row.recordings[0]
  if (!latest) return '繳交期限：未設定'
  return `最近繳交：${formatDateTime(latest.submitted_at)}（${RECORDING_STATUS_LABELS[latest.status]}）`
}

async function load() {
  window.clearTimeout(timer)
  try {
    if (!courses.value.length) {
      ;[courses.value, students.value] = await Promise.all([
        fetchMyCourses().then((list) => list.filter((item) => item.status !== 'archived')),
        fetchMyStudents(),
      ])
    }
    const lists = await Promise.all(courses.value.map((course) => fetchCourseRecordings(course.id)))
    recordings.value = lists.flat().sort((a, b) => b.submitted_at.localeCompare(a.submitted_at))
    error.value = ''
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到作業。'
  }
  // 還有錄音在分析時，每 5 秒更新一次
  if (recordings.value.some((item) => item.status === 'pending' || item.status === 'processing')) {
    timer = window.setTimeout(load, 5000)
  }
}

onMounted(load)
onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <PageHeader title="作業狀態">
    <label class="search-input">
      <span class="visually-hidden">搜尋學生</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋學生" />
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
    </label>
    <button type="button" class="btn btn--primary" @click="addOpen = true">新增</button>
  </PageHeader>

  <div class="chip-group homework__filters" role="group" aria-label="依繳交狀態篩選">
    <button
      v-for="item in filters"
      :key="item.value"
      type="button"
      class="chip"
      :aria-pressed="filter === item.value"
      @click="filter = item.value"
    >
      {{ item.label }}
    </button>
    <RouterLink v-if="route.query.course" :to="{ name: 'teacher-practice' }" class="chip">看全部課程</RouterLink>
  </div>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="shown.length === 0" class="card empty">
    {{ rows.length === 0 ? '還沒有學生加入你的課程。' : '沒有符合的作業。' }}
  </div>
  <article v-for="row in shown" :key="row.key" class="tone-card homework" :class="toneClass(row.course.id, courseKeys)">
    <p class="tone-card__cell tone-card__title homework__type">演奏作業</p>
    <div class="tone-card__cell">
      <p class="tone-card__title">{{ row.course.title }}</p>
      <p class="tone-card__line">{{ row.studentName }}</p>
    </div>
    <div class="tone-card__cell">
      <p class="tone-card__title">{{ statusText(row) }}</p>
      <p class="tone-card__line">{{ lastText(row) }}</p>
    </div>
    <button type="button" class="tone-btn" @click="detailKey = row.key">查看詳情</button>
  </article>

  <ModalPanel :open="detail !== null" :title="detail ? `${detail.course.title}｜${detail.studentName}` : ''" wide @close="detailKey = ''">
    <template v-if="detail">
      <div v-if="!detail.course.has_reference_midi" class="card homework__notice">
        這門課還沒有參考 MIDI，學生暫時不能送出練習。
        <RouterLink :to="`/teacher/courses/${detail.course.id}/edit`">到課程設定上傳</RouterLink>
      </div>
      <p v-if="detail.recordings.length === 0" class="muted">這位學生還沒有送出練習。</p>
      <article v-for="item in detail.recordings" :key="item.id" class="recording">
        <header class="recording__head">
          <strong>{{ formatDateTime(item.submitted_at) }}</strong>
        </header>
        <audio class="recording__audio" controls preload="none" :src="apiUrl(`/teacher/recordings/${item.id}/audio`)"></audio>
        <FeedbackView :recording="item" />
      </article>
    </template>
  </ModalPanel>

  <ModalPanel :open="addOpen" title="新增作業" @close="addOpen = false">
    <ul class="add">
      <li>
        <strong>演奏作業（音檔）</strong>
        <p class="muted">在課程設定上傳參考 MIDI，學生就能照著錄音繳交。</p>
        <div class="add__courses">
          <RouterLink v-for="course in courses" :key="course.id" :to="`/teacher/courses/${course.id}/edit`" class="btn btn--ghost btn--small">
            {{ course.title }}
          </RouterLink>
        </div>
      </li>
      <li>
        <strong>題庫作業（問答）</strong>
        <p class="muted">尚未開放。</p>
      </li>
    </ul>
  </ModalPanel>
</template>

<style scoped>
.search-input {
  width: min(220px, 100%);
}

.homework__filters {
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 2px solid var(--home-line);
}

.homework {
  grid-template-columns: 130px minmax(0, 0.8fr) minmax(0, 1.6fr) auto;
}

.homework__type {
  text-align: center;
}

.homework__notice {
  margin-bottom: 16px;
  background: var(--home-cream);
  font-size: 14px;
}

.homework__notice a {
  margin-left: 6px;
  color: var(--home-accent);
  text-decoration: underline;
}

.recording + .recording {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid var(--home-line);
}

.recording__audio {
  display: block;
  width: 100%;
  max-width: 420px;
  margin: 10px 0;
}

.add {
  margin: 0;
  padding: 0;
  list-style: none;
}

.add li + li {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--home-line);
}

.add p {
  margin: 4px 0 10px;
  font-size: 14px;
}

.add__courses {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
