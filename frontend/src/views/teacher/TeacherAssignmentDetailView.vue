<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import PageToolbar from '@/components/console/PageToolbar.vue'
import FeedbackView from '@/components/console/FeedbackView.vue'
import ScoreCompare from '@/components/console/ScoreCompare.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import QuizWrongList from '@/components/console/QuizWrongList.vue'
import {
  deleteAssignment,
  fetchAssignmentQuiz,
  fetchAssignmentQuizAttempts,
  fetchAssignments,
  fetchCourseRecordings,
  teacherScoreSheetUrl,
} from '@/api/teacher'
import { apiUrl } from '@/api/http'
import type { Assignment, QuizAttempt, QuizQuestion, TeacherRecording } from '@/types/api'
import { QUIZ_TYPE_LABELS, assignmentTone, dueText, formatDateTime, optionLetters } from '@/utils/format'

// 設計稿的「學生作業詳情」：這位學生的演奏作業／題庫作業兩個分頁，每份作業一張卡片，
// 按右上角放大鏡展開：演奏作業看每次錄音與回饋，題庫作業看題目與每次作答的錯題。
// 網址的 id 是目前展開的作業，「刪除作業」刪的就是它。
const route = useRoute()
const router = useRouter()
const all = ref<Assignment[]>([])
const tab = ref<Assignment['kind']>('performance')
const recordings = ref<TeacherRecording[]>([])
const questions = ref<QuizQuestion[]>([])
const attempts = ref<QuizAttempt[]>([])
const error = ref('')
const loading = ref(false)
const confirming = ref(false)
const showQuestions = ref(false)
// 正在看哪一筆的對照樂譜
const openSheet = ref('')
let timer = 0

const openId = computed(() => String(route.params.id))
const current = computed(() => all.value.find((item) => item.id === openId.value) ?? null)
const shown = computed(() =>
  current.value ? all.value.filter((item) => item.student_id === current.value!.student_id && item.kind === tab.value) : [],
)

function statusText(item: Assignment) {
  if (item.kind === 'quiz') return item.submission_count ? `學生已作答 ${item.submission_count} 次` : '學生尚未作答'
  return item.submission_count ? `學生已繳交 ${item.submission_count} 次` : '作業尚未繳交'
}

async function loadRecords() {
  window.clearTimeout(timer)
  const item = current.value
  if (!item) return
  loading.value = true
  try {
    if (item.kind === 'performance') {
      recordings.value = (await fetchCourseRecordings(item.course_id)).filter((row) => row.assignment_id === item.id)
      // 還有錄音在分析時，每 5 秒更新一次
      if (recordings.value.some((row) => row.status === 'pending' || row.status === 'processing')) {
        timer = window.setTimeout(loadRecords, 5000)
      }
    } else {
      ;[questions.value, attempts.value] = await Promise.all([fetchAssignmentQuiz(item.id), fetchAssignmentQuizAttempts(item.id)])
    }
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到繳交紀錄。'
  } finally {
    loading.value = false
  }
}

function toggle(item: Assignment) {
  if (item.id === openId.value) return
  router.replace({ name: 'teacher-assignment', params: { id: item.id } })
}

function switchTab(kind: Assignment['kind']) {
  tab.value = kind
  const first = shown.value[0]
  if (first && current.value?.kind !== kind) toggle(first)
}

async function remove() {
  confirming.value = false
  try {
    await deleteAssignment(openId.value)
    router.push('/teacher/practice')
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '作業沒有刪除。'
  }
}

watch(
  openId,
  async () => {
    error.value = ''
    recordings.value = []
    questions.value = []
    attempts.value = []
    showQuestions.value = false
    try {
      if (!all.value.some((item) => item.id === openId.value)) all.value = await fetchAssignments()
    } catch (problem) {
      error.value = problem instanceof Error ? problem.message : '讀不到作業。'
      return
    }
    if (!current.value) {
      error.value = '找不到這份作業。'
      return
    }
    tab.value = current.value.kind
    await loadRecords()
  },
  { immediate: true },
)

onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <PageHeader title="學生作業詳情" />

  <PageToolbar divider>
    <div class="chip-group" role="tablist" aria-label="作業類型">
      <button type="button" role="tab" class="chip" :aria-pressed="tab === 'performance'" :aria-selected="tab === 'performance'" @click="switchTab('performance')">
        演奏作業
      </button>
      <button type="button" role="tab" class="chip" :aria-pressed="tab === 'quiz'" :aria-selected="tab === 'quiz'" @click="switchTab('quiz')">
        題庫作業
      </button>
    </div>
    <template #actions>
      <RouterLink to="/teacher/practice" class="btn btn--ghost">返回</RouterLink>
      <button v-if="current" type="button" class="btn btn--danger" @click="confirming = true">刪除作業</button>
    </template>
  </PageToolbar>
  <p v-if="error" class="error-text" role="alert">{{ error }}</p>

  <div v-if="current && shown.length === 0" class="card empty">
    {{ current.student_name }}還沒有{{ tab === 'quiz' ? '題庫' : '演奏' }}作業。
  </div>

  <template v-for="item in shown" :key="item.id">
    <article class="tone-card detail" :class="assignmentTone(item)">
      <p class="tone-card__cell tone-card__title detail__who">{{ item.student_name }}</p>
      <div class="tone-card__cell">
        <p class="tone-card__title">作業內容</p>
        <p class="tone-card__line">{{ item.title }}</p>
      </div>
      <div class="tone-card__cell">
        <p class="tone-card__title">{{ statusText(item) }}</p>
        <p class="tone-card__line">{{ dueText(item.due_at) }}</p>
      </div>
      <button
        type="button"
        class="detail__open"
        :aria-expanded="item.id === openId"
        :aria-label="`查看「${item.title}」的${item.kind === 'quiz' ? '作答' : '繳交'}紀錄`"
        @click="toggle(item)"
      >
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
          <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4" /><path d="M8 8h6M8 12h3" />
          <circle cx="16.5" cy="16.5" r="3.5" /><path d="m19 19 2.5 2.5" />
        </svg>
      </button>
    </article>

    <template v-if="item.id === openId">
      <section v-if="item.kind === 'performance'" class="card">
        <h2 class="card__title">繳交紀錄</h2>
        <p v-if="loading && recordings.length === 0" class="muted">讀取中…</p>
        <p v-else-if="recordings.length === 0" class="muted">學生還沒有繳交。</p>
        <article v-for="row in recordings" :key="row.id" class="recording">
          <div class="recording__head">
            <strong>{{ formatDateTime(row.submitted_at) }}</strong>
            <span v-if="row.metronome_bpm" class="badge badge--soft">節拍器 {{ Math.round(row.metronome_bpm) }} BPM</span>
            <button
              v-if="row.feedback?.has_score_sheet"
              type="button"
              class="btn btn--ghost btn--small"
              :aria-expanded="openSheet === row.id"
              @click="openSheet = openSheet === row.id ? '' : row.id"
            >
              {{ openSheet === row.id ? '收起對照譜' : '看對照譜' }}
            </button>
          </div>
          <audio class="recording__audio" controls preload="none" :src="apiUrl(`/teacher/recordings/${row.id}/audio`)"></audio>
          <FeedbackView :recording="row" />
          <ScoreCompare v-if="openSheet === row.id" :url="teacherScoreSheetUrl(row.id)" />
        </article>
      </section>

      <template v-else>
        <section class="card">
          <div class="detail__bar">
            <h2 class="card__title">題目（共 {{ questions.length }} 題）</h2>
            <button type="button" class="btn btn--ghost btn--small" :aria-expanded="showQuestions" @click="showQuestions = !showQuestions">
              {{ showQuestions ? '收起題目' : '查看題目與答案' }}
            </button>
          </div>
          <ol v-if="showQuestions" class="questions">
            <li v-for="question in questions" :key="question.id">
              <p>
                <span class="badge badge--soft">{{ QUIZ_TYPE_LABELS[question.question_type] }}</span>
                {{ question.question }}
              </p>
              <p class="muted">
                {{ question.options.map((option, index) => `${String.fromCharCode(65 + index)}. ${option}`).join('　') }}
              </p>
              <p class="questions__answer">答案：{{ optionLetters(question.answers ?? []) }}</p>
            </li>
          </ol>
        </section>

        <section class="card">
          <h2 class="card__title">作答紀錄</h2>
          <p v-if="loading && attempts.length === 0" class="muted">讀取中…</p>
          <p v-else-if="attempts.length === 0" class="muted">學生還沒有作答。</p>
          <details v-for="attempt in [...attempts].reverse()" :key="attempt.id" class="attempt" :open="attempt === attempts[attempts.length - 1]">
            <summary>
              <strong>第 {{ attempt.attempt_no }} 次練習</strong>
              <span class="muted">{{ formatDateTime(attempt.submitted_at) }}・答錯 {{ attempt.wrong.length }} 題</span>
            </summary>
            <QuizWrongList :items="attempt.wrong" />
          </details>
        </section>
      </template>
    </template>
  </template>

  <NoticeDialog
    :open="confirming"
    message="刪除這份作業？"
    :detail="current?.kind === 'quiz' ? '題目與學生的作答紀錄會一起刪除。' : '參考 MIDI 與教材檔會一起刪除。學生已繳交的錄音與回饋會保留。'"
    confirm-text="刪除"
    cancel-text="取消"
    danger
    @confirm="remove"
    @cancel="confirming = false"
  />
</template>

<style scoped>
.detail {
  position: relative;
  grid-template-columns: 150px minmax(0, 1fr) minmax(0, 1.4fr) auto;
  margin-bottom: 18px;
}

.detail__who {
  text-align: center;
}

.detail__open {
  align-self: start;
  padding: 2px;
  border: 0;
  background: none;
  color: var(--tone-ink);
  opacity: 0.6;
  cursor: pointer;
}

.detail__open[aria-expanded='true'],
.detail__open:hover {
  opacity: 1;
}

.detail__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.detail__bar .card__title {
  margin: 0;
}

section.card {
  margin-bottom: 18px;
}

.recording + .recording {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid var(--home-line);
}

.recording__head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.recording__audio {
  display: block;
  width: 100%;
  max-width: 420px;
  margin: 10px 0;
}

.questions {
  margin: 12px 0 0;
  padding-left: 22px;
}

.questions li + li {
  margin-top: 12px;
}

.questions p {
  margin: 2px 0;
}

.questions__answer {
  color: #3f8f2a;
}

.attempt {
  padding: 12px 0;
  border-top: 1px solid var(--home-line);
}

.attempt summary {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  cursor: pointer;
}

@media (max-width: 720px) {
  .detail__who {
    text-align: left;
  }

  .detail__open {
    position: absolute;
    top: 14px;
    right: 16px;
  }
}
</style>
