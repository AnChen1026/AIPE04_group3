<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ModalPanel from '@/components/console/ModalPanel.vue'
import {
  createRecurringLesson,
  fetchMyStudents,
  fetchRecurringLessons,
  stopRecurringLesson,
  updateRecurringLesson,
} from '@/api/teacher'
import type { BoundStudent, RecurringLesson, RecurringSkippedWeek } from '@/types/api'
import { QUARTER_OPTIONS, RULE_WEEKDAYS, formatRange, minuteLabel } from '@/utils/format'

// 老師和學生談好的固定上課時間：選學生、星期幾、幾點，系統往後排 8 週的課
const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const rules = ref<RecurringLesson[]>([])
const students = ref<BoundStudent[]>([])
const error = ref('')
const saving = ref(false)
// 存檔後顯示排了幾堂、哪幾週因為衝突沒排成
const result = ref<{ message: string; skipped: RecurringSkippedWeek[] } | null>(null)

const choice = ref('')
const weekday = ref(0)
const start = ref(18 * 60)
const end = ref(19 * 60)
// 正在修改或停用哪一筆；已排的課由老師勾選要不要一起改、一起取消
const editing = ref<RecurringLesson | null>(null)
const stopping = ref<RecurringLesson | null>(null)
const pickedLessons = ref<string[]>([])

const options = computed(() =>
  students.value.flatMap((student) =>
    student.courses.map((course) => ({
      value: `${student.id}|${course.course_id}`,
      label: `${student.name}・${course.course_title}`,
    })),
  ),
)
const formTitle = computed(() => (editing.value ? `修改 ${editing.value.student_name} 的固定時間` : '新增固定上課時間'))

function ruleTime(rule: RecurringLesson) {
  return `${RULE_WEEKDAYS[rule.weekday]} ${minuteLabel(rule.start_minute)}－${minuteLabel(rule.end_minute)}`
}

async function reload() {
  ;[rules.value, students.value] = await Promise.all([fetchRecurringLessons(), fetchMyStudents()])
}

function resetForm() {
  editing.value = null
  stopping.value = null
  pickedLessons.value = []
  choice.value = ''
}

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    resetForm()
    result.value = null
    error.value = ''
    try {
      await reload()
    } catch (problem) {
      error.value = problem instanceof Error ? problem.message : '讀不到固定上課時間。'
    }
  },
)

function startEdit(rule: RecurringLesson) {
  stopping.value = null
  editing.value = rule
  pickedLessons.value = []
  weekday.value = rule.weekday
  start.value = rule.start_minute
  end.value = rule.end_minute
  result.value = null
}

function startStop(rule: RecurringLesson) {
  editing.value = null
  stopping.value = rule
  pickedLessons.value = []
  result.value = null
}

async function run(action: () => Promise<void>) {
  saving.value = true
  error.value = ''
  try {
    await action()
    resetForm()
    await reload()
    emit('saved')
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '沒有存成功，請再試一次。'
  } finally {
    saving.value = false
  }
}

function save() {
  error.value = ''
  if (end.value <= start.value) {
    error.value = '結束時間要晚於開始時間。'
    return
  }
  const time = { weekday: weekday.value, start_minute: start.value, end_minute: end.value }
  const rule = editing.value
  if (rule) {
    run(async () => {
      const saved = await updateRecurringLesson(rule.id, { ...time, move_lesson_ids: pickedLessons.value })
      result.value = { message: `固定時間已改好，移動了 ${saved.created} 堂課。`, skipped: saved.skipped }
    })
    return
  }
  const [studentId, courseId] = choice.value.split('|')
  if (!studentId || !courseId) {
    error.value = '請選擇學生。'
    return
  }
  run(async () => {
    const saved = await createRecurringLesson({ ...time, student_id: studentId, course_id: courseId })
    result.value = { message: `已排進課表 ${saved.created} 堂課。`, skipped: saved.skipped }
  })
}

function confirmStop() {
  const rule = stopping.value
  if (!rule) return
  const cancelled = pickedLessons.value
  run(async () => {
    await stopRecurringLesson(rule.id, cancelled)
    result.value = { message: `已停用，取消了 ${cancelled.length} 堂課，其他已排的課保留。`, skipped: [] }
  })
}
</script>

<template>
  <ModalPanel :open="open" title="固定上課時間" wide @close="emit('close')">
    <p class="muted recurring__hint">
      和學生談好後設定在這裡，系統會維持排好未來 8 週的課。學生請假或調課只影響那一堂。
    </p>

    <p v-if="result" class="recurring__notice" role="status">{{ result.message }}</p>
    <div v-if="result?.skipped.length" class="recurring__skipped" role="alert">
      <strong>這幾週有衝突，沒有排成：</strong>
      <ul>
        <li v-for="item in result.skipped" :key="item.starts_at">{{ formatRange(item.starts_at, item.ends_at) }}（{{ item.reason }}）</li>
      </ul>
    </div>

    <ul v-if="rules.length" class="recurring__rules">
      <li v-for="rule in rules" :key="rule.id">
        <span class="recurring__rule-text">
          <strong>{{ ruleTime(rule) }}</strong>
          <span class="muted">{{ rule.student_name }}・{{ rule.course_title }}</span>
        </span>
        <button type="button" class="btn btn--ghost btn--small" @click="startEdit(rule)">修改</button>
        <button type="button" class="btn btn--ghost btn--small" @click="startStop(rule)">停用</button>
      </li>
    </ul>
    <p v-else class="muted">還沒有設定固定上課時間。</p>

    <section v-if="stopping" class="recurring__form">
      <h3>停用 {{ stopping.student_name }} {{ ruleTime(stopping) }}</h3>
      <p class="muted recurring__hint">停用後不再往後排課。已排的課預設保留，勾選的才會取消。</p>
      <p v-if="stopping.future_lessons.length === 0" class="muted">沒有之後的課。</p>
      <label v-for="lesson in stopping.future_lessons" :key="lesson.id" class="recurring__lesson">
        <input v-model="pickedLessons" type="checkbox" :value="lesson.id" />
        取消 {{ formatRange(lesson.starts_at, lesson.ends_at) }}
      </label>
      <div class="recurring__actions">
        <button type="button" class="btn btn--ghost" @click="resetForm">返回</button>
        <button type="button" class="btn btn--primary" :disabled="saving" @click="confirmStop">確定停用</button>
      </div>
    </section>

    <section v-else class="recurring__form">
      <h3>{{ formTitle }}</h3>
      <div v-if="!editing" class="field">
        <label class="field__label" for="recurring-student">學生與課程</label>
        <select id="recurring-student" v-model="choice" class="select">
          <option value="" disabled>選擇已綁定的學生</option>
          <option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
        <p v-if="options.length === 0" class="muted">還沒有已綁定的學生。</p>
      </div>
      <div class="recurring__row">
        <div class="field">
          <label class="field__label" for="recurring-weekday">星期</label>
          <select id="recurring-weekday" v-model.number="weekday" class="select">
            <option v-for="(label, index) in RULE_WEEKDAYS" :key="label" :value="index">{{ label }}</option>
          </select>
        </div>
        <div class="field">
          <label class="field__label" for="recurring-start">開始</label>
          <select id="recurring-start" v-model.number="start" class="select">
            <option v-for="minute in QUARTER_OPTIONS" :key="minute" :value="minute">{{ minuteLabel(minute) }}</option>
          </select>
        </div>
        <div class="field">
          <label class="field__label" for="recurring-end">結束</label>
          <select id="recurring-end" v-model.number="end" class="select">
            <option v-for="minute in QUARTER_OPTIONS" :key="minute" :value="minute">{{ minuteLabel(minute) }}</option>
          </select>
        </div>
      </div>
      <template v-if="editing">
        <p class="muted recurring__hint">已排的課預設保留原本時間，勾選的才會移到同一週的新時間；之後新排的週都用新時間。</p>
        <label v-for="lesson in editing.future_lessons" :key="lesson.id" class="recurring__lesson">
          <input v-model="pickedLessons" type="checkbox" :value="lesson.id" />
          移動 {{ formatRange(lesson.starts_at, lesson.ends_at) }}
        </label>
      </template>
      <div class="recurring__actions">
        <button v-if="editing" type="button" class="btn btn--ghost" @click="resetForm">返回</button>
        <button type="button" class="btn btn--primary" :disabled="saving" @click="save">
          {{ saving ? '儲存中…' : editing ? '儲存修改' : '排進課表' }}
        </button>
      </div>
    </section>

    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    <template #footer>
      <button type="button" class="btn btn--ghost" @click="emit('close')">關閉</button>
    </template>
  </ModalPanel>
</template>

<style scoped>
.recurring__hint {
  margin: 0 0 12px;
  font-size: 14px;
}

.recurring__notice {
  margin: 0 0 12px;
  padding: 10px 14px;
  border-radius: 14px;
  background: var(--home-cream);
  font-size: 14px;
}

.recurring__skipped {
  margin: 0 0 12px;
  padding: 10px 14px;
  border-radius: 14px;
  background: #f5dfd2;
  color: #8a4f37;
  font-size: 14px;
}

.recurring__skipped ul {
  margin: 6px 0 0;
  padding-left: 18px;
}

.recurring__rules {
  margin: 0;
  padding: 0;
  list-style: none;
}

.recurring__rules li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-top: 1px solid var(--home-line);
}

.recurring__rules li:first-child {
  border-top: 0;
}

.recurring__rule-text {
  display: flex;
  flex: 1 1 200px;
  flex-wrap: wrap;
  gap: 4px 10px;
}

.recurring__rule-text strong {
  font-weight: 500;
}

.recurring__form {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--home-line);
}

.recurring__form h3 {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 500;
}

.recurring__row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}

.recurring__row .field {
  flex: 1 1 110px;
  margin: 0;
}

.recurring__lesson {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 0;
  font-size: 14px;
}

.recurring__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}
</style>
