<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import CalendarPager, { type CalendarMode } from '@/components/console/CalendarPager.vue'
import DayStrip from '@/components/console/DayStrip.vue'
import WeekTimetable from '@/components/console/WeekTimetable.vue'
import MonthCalendar from '@/components/console/MonthCalendar.vue'
import type { TimetableItem } from '@/components/console/timetable'
import ModalPanel from '@/components/console/ModalPanel.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { bookSlot, createChangeRequest, fetchMyChangeRequests, fetchStudentSchedule, fetchTeacherAvailability } from '@/api/student'
import { useBoundCourses } from '@/composables/useBoundCourses'
import type { AvailabilitySlot, ChangeRequest, ChangeRequestType, Conversation, Lesson } from '@/types/api'
import {
  CHANGE_STATUS_LABELS,
  CHANGE_TYPE_LABELS,
  addDays,
  formatDateTime,
  formatRange,
  formatTime,
  sameDay,
  startOfWeek,
  toLocalInput,
  toneClass,
} from '@/utils/format'

// 學生課表：所有已綁定課程的課，待老師確認的約課也一起畫上去。右上方切換日／週／月；
// 「日」是設計稿的樣子，列出那天的課，可以在那裡調課、請假
const route = useRoute()
const courses = useBoundCourses()
const lessons = ref<(Lesson & { course: Conversation })[]>([])
const requests = ref<(ChangeRequest & { course: Conversation })[]>([])
const error = ref('')
const mode = ref<CalendarMode>('week')
const anchor = ref(new Date())
const weekStart = computed(() => startOfWeek(anchor.value))

const pendingFor = (lessonId: string) =>
  requests.value.find((item) => item.session_id === lessonId && item.status === 'pending')
const courseKeys = computed(() => courses.bound.value.map((item) => item.course_id))

interface DayCard {
  key: string
  starts_at: string
  ends_at: string
  course: Conversation
  status: 'confirmed' | 'cancelled' | 'pending'
  lesson: Lesson | null
}

const STATUS_TEXT: Record<DayCard['status'], string> = { confirmed: '已確認', cancelled: '已取消', pending: '待確認' }

const allCards = computed<DayCard[]>(() => {
  const list: DayCard[] = lessons.value.map((lesson) => ({
    key: lesson.id,
    starts_at: lesson.starts_at,
    ends_at: lesson.ends_at,
    course: lesson.course,
    status: lesson.status === 'cancelled' ? 'cancelled' : 'confirmed',
    lesson,
  }))
  for (const item of requests.value) {
    if (item.request_type !== 'booking' || item.status !== 'pending' || !item.proposed_starts_at || !item.proposed_ends_at) continue
    list.push({
      key: item.id,
      starts_at: item.proposed_starts_at,
      ends_at: item.proposed_ends_at,
      course: item.course,
      status: 'pending',
      lesson: null,
    })
  }
  return list
})
const dayCards = computed(() =>
  allCards.value
    .filter((card) => sameDay(new Date(card.starts_at), anchor.value))
    .sort((a, b) => a.starts_at.localeCompare(b.starts_at)),
)
// 選一門已綁定的課，就把那位老師還開放的時段疊在自己的課表上，點一下就能預約。
// 只能透過自己已綁定的課看那位老師的時段（ADR 0009）
const SLOT_PREFIX = 'slot:'
const slotCourseId = ref('')
const slotCourse = computed(() => courses.bound.value.find((item) => item.course_id === slotCourseId.value) ?? null)
const slots = ref<AvailabilitySlot[]>([])
const slotError = ref('')
const picking = ref<AvailabilitySlot | null>(null)
const booking = ref(false)
const booked = ref('')

async function loadSlots() {
  slotError.value = ''
  if (!slotCourseId.value) {
    slots.value = []
    return
  }
  try {
    slots.value = await fetchTeacherAvailability(slotCourseId.value)
  } catch (problem) {
    slots.value = []
    slotError.value = problem instanceof Error ? problem.message : '讀不到老師的時段。'
  }
}

watch(slotCourseId, loadSlots)

const daySlots = computed(() =>
  slots.value.filter((slot) => sameDay(new Date(slot.starts_at), anchor.value)),
)

function pickSlot(id: string) {
  picking.value = slots.value.find((slot) => `${SLOT_PREFIX}${slot.id}` === id || slot.id === id) ?? null
}

async function confirmBooking() {
  const slot = picking.value
  const courseId = slotCourseId.value
  picking.value = null
  if (!slot || !courseId) return
  booking.value = true
  slotError.value = ''
  try {
    await bookSlot(courseId, slot.id)
    booked.value = formatRange(slot.starts_at, slot.ends_at)
  } catch (problem) {
    // 被別的同學搶先預約時後端回 409
    slotError.value = problem instanceof Error ? problem.message : '預約失敗，請再試一次。'
  } finally {
    booking.value = false
    await Promise.all([load(), loadSlots()])
  }
}

const items = computed<TimetableItem[]>(() => [
  ...allCards.value.map((card) => ({
    id: card.key,
    starts_at: card.starts_at,
    ends_at: card.ends_at,
    title: card.status === 'pending' ? '待完成約課' : (card.course.course_title ?? '課程'),
    subtitle: card.status === 'pending' ? `${card.course.course_title ?? ''}・等老師確認` : `${card.course.teacher_name}老師`,
    colorKey: card.course.course_id,
    cancelled: card.status === 'cancelled',
    slot: card.status === 'pending' ? ('held' as const) : undefined,
  })),
  ...slots.value.map((slot) => ({
    id: `${SLOT_PREFIX}${slot.id}`,
    starts_at: slot.starts_at,
    ends_at: slot.ends_at,
    title: '可預約',
    subtitle: slotCourse.value ? `${slotCourse.value.teacher_name}老師・點一下預約` : '點一下預約',
    colorKey: 'availability',
    slot: 'open' as const,
  })),
])

const weekDates = computed(() =>
  lessons.value
    .map((lesson) => new Date(lesson.starts_at))
    .filter((date) => date >= weekStart.value && date < addDays(weekStart.value, 7)),
)

// 「共 N 堂課，已上 M 堂」：這門課沒取消的課
function progress(course: Conversation) {
  const same = lessons.value.filter((item) => item.course_id === course.course_id && item.status === 'scheduled')
  const done = same.filter((item) => new Date(item.ends_at) < new Date()).length
  return `共 ${same.length} 堂課，已上 ${done} 堂`
}

function canChange(card: DayCard) {
  return card.lesson !== null && card.status === 'confirmed' && new Date(card.lesson.starts_at) > new Date()
}

// 週課表、月曆上點一堂課或日期：換到那天的「日」，在那裡調課、請假
function showDay(date: Date) {
  anchor.value = date
  mode.value = 'day'
}

function showCard(key: string) {
  if (key.startsWith(SLOT_PREFIX)) {
    pickSlot(key)
    return
  }
  const card = allCards.value.find((item) => item.key === key)
  if (card) showDay(new Date(card.starts_at))
}

// 申請表單：約課（新的一堂）、請假、調課
const form = reactive({
  open: false,
  type: 'booking' as ChangeRequestType,
  courseId: '',
  lesson: null as Lesson | null,
  start: '',
  minutes: 60,
  reason: '',
  error: '',
  sending: false,
})
const sent = ref(false)

async function load() {
  error.value = ''
  const bound = courses.bound.value
  try {
    const [lessonLists, requestLists] = await Promise.all([
      Promise.all(bound.map((course) => fetchStudentSchedule(course.course_id))),
      Promise.all(bound.map((course) => fetchMyChangeRequests(course.course_id))),
    ])
    lessons.value = lessonLists.flatMap((list, index) => list.map((lesson) => ({ ...lesson, course: bound[index]! })))
    requests.value = requestLists
      .flatMap((list, index) => list.map((item) => ({ ...item, course: bound[index]! })))
      .sort((a, b) => b.created_at.localeCompare(a.created_at))
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
    courseId: lesson?.course_id ?? courses.courseId.value,
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
    await createChangeRequest(form.courseId, {
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

onMounted(async () => {
  await courses.load()
  slotCourseId.value = courses.courseId.value
  await load()
  // 從「老師」頁按「上課申請」進來時，直接打開約課表單
  if (route.query.apply && courses.courseId.value) openForm('booking')
})
</script>

<template>
  <PageHeader title="課表" description="請假、調課或約新的一堂課，要等老師同意後課表才會改。">
    <CalendarPager v-model="anchor" v-model:mode="mode" />
    <button v-if="courses.bound.value.length" type="button" class="btn btn--primary" @click="openForm('booking')">新增申請</button>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div class="slot-bar">
    <label class="slot-bar__label" for="slot-course">老師可預約時段</label>
    <select v-if="courses.bound.value.length" id="slot-course" v-model="slotCourseId" class="select slot-bar__select">
      <option value="">不顯示</option>
      <option v-for="item in courses.bound.value" :key="item.course_id" :value="item.course_id">
        {{ item.course_title }}・{{ item.teacher_name }}老師
      </option>
    </select>
    <span v-else-if="courses.loaded.value" class="muted">還沒有綁定課程，先輸入老師給的綁定碼才看得到老師的時段。</span>
    <span v-if="slotCourse && slots.length === 0 && !slotError" class="muted">這位老師目前沒有開放的時段。</span>
    <span v-if="slotCourse && slots.length" class="slot-bar__legend">
      <span class="slot-bar__swatch slot-bar__swatch--open"></span>可預約
      <span class="slot-bar__swatch slot-bar__swatch--held"></span>待完成約課
    </span>
  </div>
  <p v-if="slotError" class="error-text" role="alert">{{ slotError }}</p>

  <div v-if="courses.loaded.value && courses.bound.value.length === 0" class="card empty">
    還沒有進入任何課程。先在「老師」頁輸入老師給的綁定碼，就會看到課表。
  </div>

  <template v-else>
    <WeekTimetable v-if="mode === 'week'" :week-start="weekStart" :items="items" @select="showCard" />
    <MonthCalendar v-else-if="mode === 'month'" :month="anchor" :items="items" @select="showCard" @day="showDay" />
    <template v-else>
    <DayStrip v-model="anchor" :week-start="weekStart" :marked="weekDates" />

    <div v-if="dayCards.length === 0 && daySlots.length === 0" class="card empty">這天沒有課，可以按「新增申請」向老師提出時間。</div>
    <div v-if="daySlots.length" class="card day-slots">
      <span class="muted">{{ slotCourse?.teacher_name }}老師這天可預約：</span>
      <button v-for="slot in daySlots" :key="slot.id" type="button" class="chip" :disabled="booking" @click="pickSlot(slot.id)">
        {{ formatTime(slot.starts_at) }}－{{ formatTime(slot.ends_at) }}
      </button>
    </div>
    <article
      v-for="card in dayCards"
      :key="card.key"
      class="tone-card lesson-card"
      :class="toneClass(card.course.course_id, courseKeys)"
    >
      <div class="tone-card__cell lesson-card__time">
        <p class="tone-card__title">{{ formatTime(card.starts_at) }} - {{ formatTime(card.ends_at) }}</p>
        <span class="tone-btn lesson-card__status">{{ STATUS_TEXT[card.status] }}</span>
      </div>
      <div class="tone-card__cell">
        <p class="tone-card__title">{{ card.course.course_title }}　{{ card.course.teacher_name }}老師</p>
        <p v-if="card.lesson && pendingFor(card.lesson.id)" class="tone-card__line">
          {{ CHANGE_TYPE_LABELS[pendingFor(card.lesson.id)!.request_type] }}申請中
        </p>
        <p v-else-if="canChange(card)" class="lesson-card__actions">
          <button type="button" class="tone-btn" @click="openForm('reschedule', card.lesson)">調課</button>
          <button type="button" class="tone-btn" @click="openForm('leave', card.lesson)">請假</button>
        </p>
      </div>
      <div class="tone-card__cell">
        <p class="tone-card__line">{{ progress(card.course) }}</p>
      </div>
    </article>
    </template>

    <section class="card requests-card">
      <h2 class="card__title">申請紀錄</h2>
      <p v-if="requests.length === 0" class="muted">還沒有送出申請。</p>
      <ul class="requests">
        <li v-for="item in requests" :key="item.id">
          <span class="badge badge--soft">{{ CHANGE_TYPE_LABELS[item.request_type] }}</span>
          <span>{{ item.course.course_title }}</span>
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
  </template>

  <ModalPanel :open="form.open" :title="CHANGE_TYPE_LABELS[form.type] ?? ''" @close="form.open = false">
    <form id="change-form" novalidate @submit.prevent="submit">
      <div v-if="!form.lesson && courses.bound.value.length > 1" class="field">
        <label class="field__label" for="change-course">課程</label>
        <select id="change-course" v-model="form.courseId" class="select">
          <option v-for="item in courses.bound.value" :key="item.course_id" :value="item.course_id">
            {{ item.course_title }}｜{{ item.teacher_name }} 老師
          </option>
        </select>
      </div>
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
    :open="picking !== null"
    :message="picking ? `預約 ${formatRange(picking.starts_at, picking.ends_at)}？` : ''"
    :detail="`${slotCourse?.course_title ?? ''}・${slotCourse?.teacher_name ?? ''}老師。送出後時段先保留給你，老師完成約課才會排進課表。`"
    confirm-text="預約"
    cancel-text="再想想"
    @confirm="confirmBooking"
    @cancel="picking = null"
  />

  <NoticeDialog
    :open="booked !== ''"
    message="已送出預約"
    :detail="`${booked}，等老師完成約課後會變成正式的課。`"
    @confirm="booked = ''"
    @cancel="booked = ''"
  />

  <NoticeDialog
    :open="sent"
    message="申請已送出"
    detail="老師同意之前，正式課表還不會改變。"
    @confirm="sent = false"
    @cancel="sent = false"
  />
</template>

<style scoped>
.slot-bar {
  display: flex;
  align-items: center;
  gap: 10px 14px;
  flex-wrap: wrap;
  margin-bottom: 14px;
  font-size: 14px;
}

.slot-bar__label {
  font-weight: 500;
}

.slot-bar__select {
  width: auto;
  min-width: 220px;
  max-width: 100%;
}

.slot-bar__legend {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--home-muted);
}

.slot-bar__swatch {
  display: inline-block;
  width: 14px;
  height: 14px;
  margin-left: 6px;
  border: 1.5px dashed currentColor;
  border-radius: 4px;
}

.slot-bar__swatch--open {
  background: #eef3e6;
  color: #55623f;
}

.slot-bar__swatch--held {
  background: #fbefd9;
  color: #8a5a1f;
}

.day-slots {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.lesson-card {
  grid-template-columns: 170px minmax(0, 1.4fr) minmax(0, 1fr);
}

.lesson-card__time {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.lesson-card__status {
  cursor: default;
}

.lesson-card__actions {
  display: flex;
  gap: 8px;
  margin: 8px 0 0;
}

.requests-card {
  margin-top: 22px;
}

.requests {
  margin: 0;
  padding: 0;
  list-style: none;
}

.requests li {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 0;
  border-top: 1px solid var(--home-line);
}

.requests li:first-child {
  border-top: 0;
}

.requests__status {
  margin-left: auto;
}

@media (max-width: 720px) {
  .lesson-card__time {
    align-items: flex-start;
  }
}
</style>
