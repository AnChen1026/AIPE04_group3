<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import CoursePicker from '@/components/console/CoursePicker.vue'
import ModalPanel from '@/components/console/ModalPanel.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { createChangeRequest, fetchMyChangeRequests, fetchStudentSchedule } from '@/api/student'
import { useBoundCourses } from '@/composables/useBoundCourses'
import type { ChangeRequest, ChangeRequestType, Lesson } from '@/types/api'
import {
  CHANGE_STATUS_LABELS,
  CHANGE_TYPE_LABELS,
  formatDateTime,
  formatRange,
  toLocalInput,
} from '@/utils/format'

const courses = useBoundCourses()
const lessons = ref<Lesson[]>([])
const requests = ref<ChangeRequest[]>([])
const error = ref('')

const upcoming = computed(() => lessons.value.filter((lesson) => new Date(lesson.ends_at) > new Date()))
const past = computed(() => lessons.value.filter((lesson) => new Date(lesson.ends_at) <= new Date()).reverse())
const pendingFor = (lessonId: string) =>
  requests.value.find((item) => item.session_id === lessonId && item.status === 'pending')

// 申請表單：約課（新的一堂）、請假、調課
const form = reactive({
  open: false,
  type: 'booking' as ChangeRequestType,
  lesson: null as Lesson | null,
  start: '',
  minutes: 60,
  reason: '',
  error: '',
  sending: false,
})
const sent = ref(false)

async function load() {
  if (!courses.courseId.value) return
  error.value = ''
  try {
    ;[lessons.value, requests.value] = await Promise.all([
      fetchStudentSchedule(courses.courseId.value),
      fetchMyChangeRequests(courses.courseId.value),
    ])
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到課表。'
  }
}

function openForm(type: ChangeRequestType, lesson: Lesson | null = null) {
  const start = lesson ? new Date(lesson.starts_at) : new Date(Date.now() + 7 * 86_400_000)
  if (!lesson) start.setMinutes(0, 0, 0)
  Object.assign(form, {
    open: true,
    type,
    lesson,
    start: toLocalInput(start),
    minutes: lesson ? Math.round((new Date(lesson.ends_at).getTime() - start.getTime()) / 60_000) : 60,
    reason: '',
    error: '',
  })
}

async function submit() {
  form.error = ''
  const needsTime = form.type !== 'leave'
  const start = new Date(form.start)
  if (needsTime && (Number.isNaN(start.getTime()) || start <= new Date())) {
    form.error = '請選擇之後的時間。'
    return
  }
  form.sending = true
  try {
    await createChangeRequest(courses.courseId.value, {
      request_type: form.type,
      session_id: form.lesson?.id ?? null,
      proposed_starts_at: needsTime ? start.toISOString() : null,
      proposed_ends_at: needsTime ? new Date(start.getTime() + form.minutes * 60_000).toISOString() : null,
      reason: form.reason.trim() || null,
    })
    form.open = false
    sent.value = true
    await load()
  } catch (problem) {
    form.error = problem instanceof Error ? problem.message : '申請沒有送出。'
  } finally {
    form.sending = false
  }
}

watch(() => courses.courseId.value, load)
onMounted(async () => {
  await courses.load()
  await load()
})
</script>

<template>
  <PageHeader title="課表" description="請假、調課或約新的一堂課，要等老師同意後課表才會改。">
    <CoursePicker v-model="courses.courseId.value" :courses="courses.bound.value" />
    <button v-if="courses.courseId.value" type="button" class="btn btn--primary" @click="openForm('booking')">約一堂課</button>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="courses.loaded.value && courses.bound.value.length === 0" class="card empty">
    還沒有進入任何課程。先在「我的課程」和老師聊聊，輸入綁定碼後就會看到課表。
  </div>

  <template v-else>
    <section class="card">
      <h2 class="card__title">接下來的課</h2>
      <p v-if="upcoming.length === 0" class="muted">還沒有排定的課，可以按「約一堂課」向老師提出時間。</p>
      <ul class="lessons">
        <li v-for="lesson in upcoming" :key="lesson.id">
          <span class="lessons__time">{{ formatRange(lesson.starts_at, lesson.ends_at) }}</span>
          <span v-if="pendingFor(lesson.id)" class="badge badge--warn">
            {{ CHANGE_TYPE_LABELS[pendingFor(lesson.id)!.request_type] }}申請中
          </span>
          <span v-else class="lessons__actions">
            <button type="button" class="btn btn--ghost btn--small" @click="openForm('reschedule', lesson)">調課</button>
            <button type="button" class="btn btn--ghost btn--small" @click="openForm('leave', lesson)">請假</button>
          </span>
        </li>
      </ul>
    </section>

    <section class="card">
      <h2 class="card__title">申請紀錄</h2>
      <p v-if="requests.length === 0" class="muted">還沒有送出申請。</p>
      <ul class="requests">
        <li v-for="item in requests" :key="item.id">
          <span class="badge badge--soft">{{ CHANGE_TYPE_LABELS[item.request_type] }}</span>
          <span v-if="item.proposed_starts_at && item.proposed_ends_at">{{ formatRange(item.proposed_starts_at, item.proposed_ends_at) }}</span>
          <span v-else class="muted">送出於 {{ formatDateTime(item.created_at) }}</span>
          <span
            class="badge requests__status"
            :class="{ 'badge--accent': item.status === 'approved', 'badge--error': item.status === 'rejected', 'badge--warn': item.status === 'pending' }"
          >
            {{ CHANGE_STATUS_LABELS[item.status] }}
          </span>
        </li>
      </ul>
    </section>

    <section v-if="past.length" class="card">
      <h2 class="card__title">上過的課</h2>
      <ul class="lessons">
        <li v-for="lesson in past" :key="lesson.id" class="muted">{{ formatRange(lesson.starts_at, lesson.ends_at) }}</li>
      </ul>
    </section>
  </template>

  <ModalPanel :open="form.open" :title="CHANGE_TYPE_LABELS[form.type] ?? ''" @close="form.open = false">
    <form id="change-form" novalidate @submit.prevent="submit">
      <p v-if="form.lesson" class="muted">原本：{{ formatRange(form.lesson.starts_at, form.lesson.ends_at) }}</p>
      <template v-if="form.type !== 'leave'">
        <div class="field">
          <label class="field__label" for="change-start">{{ form.type === 'booking' ? '想上課的時間' : '改到' }}</label>
          <input id="change-start" v-model="form.start" class="input" type="datetime-local" />
        </div>
        <div class="field">
          <label class="field__label" for="change-minutes">上課長度</label>
          <select id="change-minutes" v-model.number="form.minutes" class="select">
            <option :value="30">30 分鐘</option>
            <option :value="45">45 分鐘</option>
            <option :value="50">50 分鐘</option>
            <option :value="60">60 分鐘</option>
            <option :value="90">90 分鐘</option>
          </select>
        </div>
      </template>
      <div class="field">
        <label class="field__label" for="change-reason">{{ form.type === 'leave' ? '請假原因' : '想跟老師說的話（選填）' }}</label>
        <textarea id="change-reason" v-model="form.reason" class="textarea"></textarea>
      </div>
      <p v-if="form.error" class="error-text" role="alert">{{ form.error }}</p>
    </form>
    <template #footer>
      <button type="button" class="btn btn--ghost" @click="form.open = false">取消</button>
      <button type="submit" form="change-form" class="btn btn--primary" :disabled="form.sending">送出申請</button>
    </template>
  </ModalPanel>

  <NoticeDialog
    :open="sent"
    message="申請已送出"
    detail="老師同意之前，正式課表還不會改變。"
    @confirm="sent = false"
    @cancel="sent = false"
  />
</template>

<style scoped>
.lessons,
.requests {
  margin: 0;
  padding: 0;
  list-style: none;
}

.lessons li,
.requests li {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 0;
  border-top: 1px solid var(--home-line);
}

.lessons li:first-child,
.requests li:first-child {
  border-top: 0;
}

.lessons__time {
  font-variant-numeric: tabular-nums;
}

.lessons__actions,
.requests__status {
  margin-left: auto;
}

.lessons__actions {
  display: flex;
  gap: 8px;
}
</style>
