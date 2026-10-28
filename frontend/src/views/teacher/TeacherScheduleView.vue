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
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import {
  cancelTeacherLesson,
  createSlot,
  createTeacherLesson,
  decideChangeRequest,
  deleteSlot,
  fetchChangeRequests,
  fetchLessonSummary,
  fetchMyLessons,
  fetchMySlots,
  fetchMyStudents,
  moveSlot,
  releaseSlot,
} from '@/api/teacher'
import type { BoundStudent, LessonSummary, TeacherAvailabilitySlot, TeacherChangeRequest, TeacherLesson } from '@/types/api'
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
const slots = ref<TeacherAvailabilitySlot[]>([])

const selected = ref<TeacherLesson | null>(null)
const summary = ref<LessonSummary | null>(null)
const summaryLoading = ref(false)
const summaryError = ref('')

// 課表上的色塊：正式的課，加上還沒排成課的可上課時段（已排的時段畫成那堂課）
const SLOT_PREFIX = 'slot:'
const items = computed<TimetableItem[]>(() => [
  ...lessons.value.map((lesson) => ({
    id: lesson.id,
    starts_at: lesson.starts_at,
    ends_at: lesson.ends_at,
    title: lesson.course_title,
    subtitle: lesson.student_name,
    colorKey: lesson.course_id,
    cancelled: lesson.status === 'cancelled',
  })),
  ...slots.value
    .filter((slot) => slot.status !== 'booked')
    .map((slot) => ({
      id: `${SLOT_PREFIX}${slot.id}`,
      starts_at: slot.starts_at,
      ends_at: slot.ends_at,
      title: slot.status === 'open' ? '可預約' : '待完成約課',
      subtitle: slot.status === 'held' ? `${slot.student_name ?? '學生'}・${slot.course_title ?? ''}` : undefined,
      colorKey: 'availability',
      slot: slot.status as 'open' | 'held',
      draggable: slot.status === 'open',
    })),
])

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
    ;[lessons.value, requests.value, slots.value] = await Promise.all([fetchMyLessons(), fetchChangeRequests(), fetchMySlots()])
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到課表。'
  }
}

// ---------- 編輯時段：把上方三種框拖到週課表上
// 可預約：拖到空格新增一小時的時段；已有的可預約框可以拖到別的格子
// 已預約：拖到空格或可預約框，選學生後直接排進課表；拖到待完成約課的框就是完成約課
// 取消預約：拖到框上。可預約的刪掉；待完成約課的退回；已排的課取消，來自時段的話時段回到可預約
const editing = ref(false)
const editError = ref('')
const PALETTE_ITEMS = [
  { data: 'new:open', label: '可預約', className: 'palette__item--open' },
  { data: 'new:booked', label: '已預約', className: 'palette__item--booked' },
  { data: 'new:cancel', label: '取消預約', className: 'palette__item--cancel' },
] as const

function toggleEditing() {
  editing.value = !editing.value
  editError.value = ''
  if (editing.value) mode.value = 'week'
}

function onPaletteDragStart(event: DragEvent, data: string) {
  event.dataTransfer?.setData('text/plain', data)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'copyMove'
}

const slotOf = (itemId: string) =>
  itemId.startsWith(SLOT_PREFIX) ? slots.value.find((slot) => `${SLOT_PREFIX}${slot.id}` === itemId) ?? null : null

const hourLater = (at: Date) => new Date(at.getTime() + 3_600_000)

async function run(action: () => Promise<unknown>) {
  editError.value = ''
  try {
    await action()
  } catch (problem) {
    editError.value = problem instanceof Error ? problem.message : '沒有改成功，請再試一次。'
  } finally {
    await load()
  }
}

function moveTo(slot: TeacherAvailabilitySlot, at: Date) {
  const length = new Date(slot.ends_at).getTime() - new Date(slot.starts_at).getTime()
  return run(() => moveSlot(slot.id, at.toISOString(), new Date(at.getTime() + length).toISOString()))
}

function onDrop(at: Date, data: string) {
  if (at <= new Date()) {
    editError.value = '不能設定已經過去的時間。'
    return
  }
  if (data === 'new:open') run(() => createSlot(at.toISOString(), hourLater(at).toISOString()))
  else if (data === 'new:booked') openPicker(at, hourLater(at), null)
  else if (data === 'new:cancel') editError.value = '把「取消預約」拖到要取消的時段或課上。'
  else {
    const slot = slotOf(data)
    if (slot) moveTo(slot, at)
  }
}

function onDropOnItem(itemId: string, data: string, at: Date) {
  const slot = slotOf(itemId)
  const lesson = slot ? null : lessons.value.find((item) => item.id === itemId) ?? null
  if (data.startsWith(SLOT_PREFIX)) {
    // 拖動時段時放在自己身上，就是移到那一格
    if (data === itemId && slot && at > new Date()) moveTo(slot, at)
    else if (data !== itemId) editError.value = '這段時間已經有時段或課了。'
  } else if (data === 'new:open') {
    editError.value = '這段時間已經有時段或課了。'
  } else if (data === 'new:booked') {
    if (slot?.status === 'open') openPicker(new Date(slot.starts_at), new Date(slot.ends_at), slot)
    else if (slot?.status === 'held' && slot.change_request_id) {
      const requestId = slot.change_request_id
      ask(`完成 ${slot.student_name ?? '學生'} 的約課？`, formatRange(slot.starts_at, slot.ends_at), () => decideChangeRequest(requestId, true))
    } else editError.value = '這堂課已經排好了。'
  } else if (data === 'new:cancel') {
    if (slot?.status === 'open') {
      ask('刪除這個可預約時段？', formatRange(slot.starts_at, slot.ends_at), () => deleteSlot(slot.id))
    } else if (slot?.status === 'held') {
      ask(`退回 ${slot.student_name ?? '學生'} 的預約？`, '時段會回到可預約。', () => releaseSlot(slot.id))
    } else if (lesson?.status === 'scheduled') {
      const fromSlot = slots.value.find((item) => item.lesson_id === lesson.id)
      ask(
        `取消 ${lesson.student_name} 的這堂課？`,
        `${formatRange(lesson.starts_at, lesson.ends_at)}${fromSlot ? '，時段會回到可預約' : ''}。`,
        () => (fromSlot ? releaseSlot(fromSlot.id) : cancelTeacherLesson(lesson.id)),
      )
    }
  }
}

// 取消、刪除、完成約課前先確認
const confirming = ref<{ message: string; detail: string; action: () => Promise<unknown> } | null>(null)

function ask(message: string, detail: string, action: () => Promise<unknown>) {
  confirming.value = { message, detail, action }
}

function confirmAction() {
  const action = confirming.value?.action
  confirming.value = null
  if (action) run(action)
}

// 「已預約」拖下去後選是哪位學生、哪門課
const students = ref<BoundStudent[]>([])
const picker = ref<{ starts: Date; ends: Date; slot: TeacherAvailabilitySlot | null } | null>(null)
const pickerChoice = ref('')
const pickerError = ref('')
const pickerSaving = ref(false)
const pickerOptions = computed(() =>
  students.value.flatMap((student) =>
    student.courses.map((course) => ({
      value: `${student.id}|${course.course_id}`,
      label: `${student.name}・${course.course_title}`,
    })),
  ),
)

async function openPicker(starts: Date, ends: Date, slot: TeacherAvailabilitySlot | null) {
  picker.value = { starts, ends, slot }
  pickerChoice.value = ''
  pickerError.value = ''
  try {
    students.value = await fetchMyStudents()
  } catch (problem) {
    pickerError.value = problem instanceof Error ? problem.message : '讀不到學生名單。'
  }
}

async function savePicker() {
  const target = picker.value
  if (!target) return
  const [studentId, courseId] = pickerChoice.value.split('|')
  if (!studentId || !courseId) {
    pickerError.value = '請選擇學生。'
    return
  }
  pickerSaving.value = true
  pickerError.value = ''
  try {
    await createTeacherLesson({
      student_id: studentId,
      course_id: courseId,
      starts_at: target.starts.toISOString(),
      ends_at: target.ends.toISOString(),
      slot_id: target.slot?.id ?? null,
    })
    picker.value = null
    await load()
  } catch (problem) {
    pickerError.value = problem instanceof Error ? problem.message : '排課失敗，請再試一次。'
  } finally {
    pickerSaving.value = false
  }
}

async function openLesson(id: string) {
  if (id.startsWith(SLOT_PREFIX)) return
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
  <PageHeader
    title="課表"
    description="點一堂課可以看課前摘要。學生的約課、請假、調課要在這裡確認後才會改動課表。按「編輯時段」開放可上課時段給已綁定的學生預約。"
  >
    <template #title-actions>
      <button type="button" class="btn btn--primary" :aria-pressed="editing" @click="toggleEditing">
        {{ editing ? '完成編輯' : '編輯時段' }}
      </button>
    </template>
    <CalendarPager v-model="anchor" v-model:mode="mode" />
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <!-- 編輯時段時三種框放在週課表右側並固定住，捲到晚上的時段也拖得到；窄螢幕改放上方 -->
  <div class="schedule" :class="{ 'schedule--editing': editing && mode === 'week' }">
  <section v-if="editing" class="card palette" aria-label="編輯時段">
    <div class="palette__items">
      <span
        v-for="item in PALETTE_ITEMS"
        :key="item.data"
        class="palette__item"
        :class="item.className"
        draggable="true"
        @dragstart="onPaletteDragStart($event, item.data)"
      >
        {{ item.label }}
      </span>
    </div>
    <p class="muted palette__hint">
      把「可預約」拖到格子開放一小時，可預約的框也能直接拖到別的格子；
      和學生約好了就把「已預約」拖過去選學生；「取消預約」拖到框上取消。
    </p>
    <p v-if="editError" class="error-text" role="alert">{{ editError }}</p>
  </section>

  <WeekTimetable
    v-if="mode === 'week'"
    :week-start="weekStart"
    :items="items"
    :editable="editing"
    @select="openLesson"
    @drop="onDrop"
    @drop-on-item="onDropOnItem"
  />
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
  </div>

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
          <button type="button" class="btn btn--primary btn--small" :disabled="deciding === item.id" @click="decide(item, true)">
            {{ item.request_type === 'booking' ? '完成約課' : '同意' }}
          </button>
        </div>
      </li>
    </ul>
  </section>

  <ModalPanel :open="picker !== null" title="排課給哪位學生？" @close="picker = null">
    <template v-if="picker">
      <p class="lesson__time">{{ formatRange(picker.starts.toISOString(), picker.ends.toISOString()) }}</p>
      <label class="field picker__field">
        <span>學生與課程</span>
        <select v-model="pickerChoice" class="input">
          <option value="" disabled>選擇已綁定的學生</option>
          <option v-for="option in pickerOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
      </label>
      <p v-if="pickerOptions.length === 0 && !pickerError" class="muted">還沒有已綁定的學生。</p>
      <p v-if="pickerError" class="error-text" role="alert">{{ pickerError }}</p>
    </template>
    <template #footer>
      <button type="button" class="btn btn--ghost" @click="picker = null">取消</button>
      <button type="button" class="btn btn--primary" :disabled="pickerSaving" @click="savePicker">
        {{ pickerSaving ? '排課中…' : '排進課表' }}
      </button>
    </template>
  </ModalPanel>

  <NoticeDialog
    :open="confirming !== null"
    :message="confirming?.message ?? ''"
    :detail="confirming?.detail"
    confirm-text="確定"
    cancel-text="不要"
    danger
    @confirm="confirmAction"
    @cancel="confirming = null"
  />

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
.schedule--editing {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 168px;
  gap: 14px;
  align-items: start;
}

.schedule--editing .palette {
  position: sticky;
  top: 16px;
  grid-column: 2;
  grid-row: 1;
}

.palette {
  display: grid;
  gap: 10px;
  margin-bottom: 14px;
  padding: 16px;
}

.schedule--editing .palette {
  margin-bottom: 0;
}

.palette__items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.palette__item {
  padding: 8px 16px;
  text-align: center;
  border: 1.5px dashed currentColor;
  border-radius: 12px;
  font-size: 14px;
  cursor: grab;
  user-select: none;
}

.palette__item--open {
  background: #eef3e6;
  color: #55623f;
}

.palette__item--booked {
  border-style: solid;
  background: #efe2cf;
  color: #6f5238;
}

.palette__item--cancel {
  background: #f5dfd2;
  color: #8a4f37;
}

.palette__hint {
  margin: 0;
  font-size: 13px;
}

.picker__field {
  display: grid;
  gap: 6px;
  margin-top: 12px;
}

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

@media (max-width: 860px) {
  .schedule--editing {
    grid-template-columns: minmax(0, 1fr);
  }

  .schedule--editing .palette {
    position: static;
    grid-column: auto;
    grid-row: auto;
  }

  .palette__items {
    flex-direction: row;
    flex-wrap: wrap;
  }
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
