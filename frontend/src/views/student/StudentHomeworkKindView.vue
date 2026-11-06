<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import PageToolbar from '@/components/console/PageToolbar.vue'
import { fetchAssignmentRecordings, fetchMyAssignments, fetchQuizAttempts } from '@/api/student'
import type { Assignment } from '@/types/api'
import { KIND_INFO, type AnalysisKind, type PracticeAttempt } from '@/composables/useAssignmentAttempts'
import { dateOnly, dueText } from '@/utils/format'

// 設計稿「學生-作業分析」「學生-作業分析-題庫作業」：選了演奏或題庫之後，每份作業一張卡，
// 上半是「作業狀態」（有沒有繳交、期限、去上傳或作答），下半是「作業分析」（每一次練習，可以看分析、和上一次對比）
const route = useRoute()
const kind = computed(() => (route.params.kind === 'quiz' ? 'quiz' : 'performance') as AnalysisKind)
const info = computed(() => KIND_INFO[kind.value])

const assignments = ref<Assignment[]>([])
const attempts = ref<Record<string, PracticeAttempt[]>>({})
const filter = ref<'all' | 'submitted' | 'missing'>('all')
const loaded = ref(false)
const error = ref('')
// 收合狀態：作業本身、以及每份作業裡的「作業狀態」「作業分析」
const closed = ref(new Set<string>())

const FILTERS = [
  { value: 'all', label: '全部' },
  { value: 'submitted', label: '已繳交' },
  { value: 'missing', label: '未繳交' },
] as const

const ORDINALS = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
const ordinal = (no: number) => (no <= 10 ? ORDINALS[no - 1] : String(no))

const shown = computed(() =>
  assignments.value.filter((item) => filter.value === 'all' || (filter.value === 'submitted') === item.submission_count > 0),
)

function isOpen(key: string) {
  return !closed.value.has(key)
}

function toggle(key: string) {
  const next = new Set(closed.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  closed.value = next
}

function statusText(item: Assignment) {
  if (item.submission_count === 0) return '未繳交'
  return kind.value === 'quiz' ? `已作答 ${item.submission_count} 次` : '已繳交'
}

async function load() {
  loaded.value = false
  error.value = ''
  try {
    const list = (await fetchMyAssignments()).filter((item) => item.kind === kind.value)
    // 期限近的排前面，沒有期限的放最後
    assignments.value = list.sort((a, b) => (a.due_at ?? '9999').localeCompare(b.due_at ?? '9999'))
    // 第一份展開，其他先收起來，作業多時不會一頁拉很長
    closed.value = new Set(assignments.value.slice(1).map((item) => item.id))
    const lists = await Promise.all(
      assignments.value.map(async (item): Promise<PracticeAttempt[]> => {
        if (item.submission_count === 0) return []
        if (item.kind === 'quiz') {
          return (await fetchQuizAttempts(item.id)).map((row) => ({ no: row.attempt_no, submittedAt: row.submitted_at, quiz: row }))
        }
        const recordings = [...(await fetchAssignmentRecordings(item.id))].sort((a, b) => a.submitted_at.localeCompare(b.submitted_at))
        return recordings.map((row, index) => ({ no: index + 1, submittedAt: row.submitted_at, recording: row }))
      }),
    )
    attempts.value = Object.fromEntries(assignments.value.map((item, index) => [item.id, lists[index]!]))
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到作業。'
  } finally {
    loaded.value = true
  }
}

watch(kind, load, { immediate: true })
</script>

<template>
  <PageHeader title="作業" />

  <div class="kind-bar" :class="`kind-bar--${kind}`">
    <h2>
      <span class="kind-bar__icon" aria-hidden="true">{{ info.icon }}</span>
      {{ info.label }}
      <small>{{ info.hint }}</small>
    </h2>
    <RouterLink :to="{ name: 'student-homework-kind', params: { kind: info.other } }" class="kind-bar__switch">
      切換至{{ KIND_INFO[info.other].label }}
    </RouterLink>
  </div>

  <PageToolbar>
    <div class="chip-group" role="group" aria-label="依繳交狀態篩選">
      <button v-for="item in FILTERS" :key="item.value" type="button" class="chip" :aria-pressed="filter === item.value" @click="filter = item.value">
        {{ item.label }}
      </button>
    </div>
    <template #actions>
      <RouterLink :to="{ name: 'student-homework' }" class="btn btn--primary">返回</RouterLink>
    </template>
  </PageToolbar>
  <p v-if="error" class="error-text" role="alert">{{ error }}</p>

  <div v-if="loaded && assignments.length === 0" class="card empty">老師還沒有發{{ info.label }}給你。老師發布後，會出現在這裡。</div>
  <div v-else-if="loaded && shown.length === 0" class="card empty">沒有符合的作業。</div>

  <section v-for="(item, index) in shown" :key="item.id" class="work" :class="`work--${kind}`">
    <button type="button" class="work__head" :aria-expanded="isOpen(item.id)" @click="toggle(item.id)">
      <span class="work__no">{{ index + 1 }}</span>
      <span class="work__title">{{ item.title }}</span>
      <span class="caret" aria-hidden="true"></span>
      <span class="work__course">{{ item.course_title }}・{{ item.teacher_name }}老師</span>
    </button>

    <div v-if="isOpen(item.id)" class="work__body">
      <button type="button" class="work__section" :aria-expanded="isOpen(`${item.id}:status`)" @click="toggle(`${item.id}:status`)">
        作業狀態 <span class="caret" aria-hidden="true"></span>
      </button>
      <div v-if="isOpen(`${item.id}:status`)" class="work__panel">
        <div class="work__row">
          <strong class="work__cell">{{ statusText(item) }}</strong>
          <span class="work__cell work__cell--grow">{{ dueText(item.due_at) }}</span>
          <RouterLink v-if="kind === 'performance'" :to="{ name: 'student-assignment', params: { id: item.id } }" class="work__btn">
            作業上傳
          </RouterLink>
          <RouterLink v-else :to="{ name: 'student-quiz', params: { id: item.id } }" class="work__btn">
            {{ item.submission_count ? '再測驗一次' : '開始測驗' }}
          </RouterLink>
        </div>
      </div>

      <button type="button" class="work__section" :aria-expanded="isOpen(`${item.id}:analysis`)" @click="toggle(`${item.id}:analysis`)">
        作業分析 <span class="caret" aria-hidden="true"></span>
      </button>
      <div v-if="isOpen(`${item.id}:analysis`)" class="work__panel">
        <p v-if="!(attempts[item.id]?.length)" class="work__empty">
          還沒有練習紀錄，{{ kind === 'quiz' ? '測驗' : '上傳作業' }}後這裡會出現每一次的分析。
        </p>
        <div v-for="attempt in attempts[item.id]" :key="attempt.no" class="work__row">
          <strong class="work__cell">第{{ ordinal(attempt.no) }}次練習</strong>
          <span class="work__cell work__cell--grow">上傳日期 {{ dateOnly(attempt.submittedAt) }}</span>
          <span class="work__btns">
            <RouterLink :to="{ name: 'student-analysis-detail', params: { kind, id: item.id, attempt: attempt.no } }" class="work__btn">
              作業分析
            </RouterLink>
            <RouterLink
              v-if="attempt.no > 1"
              :to="{ name: 'student-analysis-compare', params: { kind, id: item.id, attempt: attempt.no } }"
              class="work__btn"
            >
              練習對比
            </RouterLink>
          </span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.kind-bar {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--home-line);
}

.kind-bar h2 {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 0;
  font-size: 22px;
  font-weight: 500;
}

.kind-bar small {
  color: var(--home-muted);
  font-size: 15px;
}

.kind-bar--performance h2 {
  color: #3f8f2a;
}

.kind-bar--quiz h2 {
  color: #1f66b8;
}

.kind-bar__switch {
  color: var(--home-muted);
  font-size: 14px;
}

.kind-bar__switch:hover {
  color: var(--home-accent);
}

/* 演奏作業用橘色、題庫作業用綠色（設計稿） */
.work {
  --work-bg: #fdecd2;
  --work-ink: #c08a52;
  --work-line: #f3cf9f;
  --work-btn: #f5c48f;
  margin-bottom: 22px;
}

.work--quiz {
  --work-bg: #e9eedf;
  --work-ink: #3f8f2a;
  --work-line: #9fc07a;
  --work-btn: #8db33f;
}

.caret {
  display: inline-block;
  width: 0;
  height: 0;
  margin-left: 4px;
  border-top: 7px solid currentColor;
  border-right: 5px solid transparent;
  border-left: 5px solid transparent;
  vertical-align: middle;
  transition: transform 0.15s ease;
}

[aria-expanded='false'] > .caret {
  transform: rotate(-90deg);
}

.work__head {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  width: 100%;
  margin-bottom: 10px;
  padding: 0;
  border: 0;
  background: none;
  color: var(--home-ink);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.work__no {
  font-size: 18px;
}

.work__title {
  color: var(--work-ink);
  font-size: 20px;
  font-weight: 700;
}

.work__head .caret {
  color: var(--home-ink);
}

.work__course {
  margin-left: auto;
  color: var(--home-muted);
  font-size: 13px;
}

.work__body {
  padding: 14px 18px 18px;
  border: 1.5px solid var(--work-line);
  border-radius: 24px;
  background: var(--work-bg);
}

.work__section {
  margin: 4px 0 8px;
  padding: 0;
  border: 0;
  background: none;
  color: var(--work-ink);
  font: inherit;
  font-size: 17px;
  font-weight: 700;
  cursor: pointer;
}

.work__panel {
  margin-bottom: 12px;
  padding: 4px 22px;
  border: 1px solid color-mix(in srgb, var(--work-ink) 30%, transparent);
  border-radius: 26px;
  background: var(--home-paper);
}

.work__row {
  display: flex;
  align-items: center;
  gap: 8px 16px;
  flex-wrap: wrap;
  padding: 10px 0;
  color: var(--work-ink);
}

.work__row + .work__row {
  border-top: 1px solid color-mix(in srgb, var(--work-ink) 30%, transparent);
}

.work__cell {
  min-width: 96px;
}

.work__cell--grow {
  flex: 1;
  padding-left: 16px;
  border-left: 1px solid color-mix(in srgb, var(--work-ink) 40%, transparent);
}

.work__btns {
  display: flex;
  gap: 8px;
}

.work__btn {
  padding: 4px 14px;
  border-radius: var(--radius-pill);
  background: var(--work-btn);
  color: color-mix(in srgb, var(--work-ink) 55%, #000);
  font-size: 14px;
  font-weight: 700;
  white-space: nowrap;
}

.work__btn:hover {
  filter: brightness(0.96);
}

.work__empty {
  margin: 0;
  padding: 12px 0;
  color: var(--home-muted);
  font-size: 14px;
}

@media (max-width: 640px) {
  .work__cell--grow {
    flex-basis: 100%;
    padding-left: 0;
    border-left: 0;
  }

  .work__course {
    margin-left: 0;
    flex-basis: 100%;
  }
}
</style>
