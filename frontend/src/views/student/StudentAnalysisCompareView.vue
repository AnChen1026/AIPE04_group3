<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import FeedbackView from '@/components/console/FeedbackView.vue'
import ScoreCompare from '@/components/console/ScoreCompare.vue'
import { studentScoreSheetUrl } from '@/api/student'
import { KIND_INFO, useAssignmentAttempts, type AnalysisKind } from '@/composables/useAssignmentAttempts'
import type { QuizWrongAnswer } from '@/types/api'
import { dateOnly } from '@/utils/format'

// 設計稿「作業分析-練習對比」：這一次和上一次比。
// 題庫作業：列出兩次各自答錯的題目，再整理「練習進步摘要」（改對了、還是錯、新錯的）。
// 演奏作業：上下列出兩次的對照樂譜與回饋。
const route = useRoute()
const kind = computed(() => (route.params.kind === 'quiz' ? 'quiz' : 'performance') as AnalysisKind)
const info = computed(() => KIND_INFO[kind.value])
const assignmentId = String(route.params.id)
const attemptNo = Number(route.params.attempt)
const { assignment, attempts, error, loaded, load } = useAssignmentAttempts(assignmentId)

const current = computed(() => attempts.value.find((item) => item.no === attemptNo) ?? null)
const previous = computed(() => attempts.value.find((item) => item.no === attemptNo - 1) ?? null)
const pair = computed(() => [previous.value, current.value].filter((item) => item !== null))

function positions(items: QuizWrongAnswer[] | undefined) {
  return new Set((items ?? []).map((item) => item.position))
}

// 練習進步摘要：只看題號，跟上一次比
const summary = computed(() => {
  if (!previous.value?.quiz || !current.value?.quiz) return []
  const before = positions(previous.value.quiz.wrong)
  const now = positions(current.value.quiz.wrong)
  const fixed = [...before].filter((item) => !now.has(item))
  const still = [...now].filter((item) => before.has(item))
  const fresh = [...now].filter((item) => !before.has(item))
  const lines: string[] = []
  if (fixed.length) lines.push(`第 ${fixed.join('、')} 題上次錯、這次改對了。`)
  if (still.length) lines.push(`第 ${still.join('、')} 題兩次都錯，需多加強相關知識。`)
  if (fresh.length) lines.push(`第 ${fresh.join('、')} 題上次對、這次錯了，再複習一次。`)
  if (!now.size) lines.push('這次全部答對了！')
  return lines
})

onMounted(load)
</script>

<template>
  <PageHeader :title="assignment ? `${assignment.course_title} - ${assignment.title}` : '練習對比'">
    <RouterLink :to="{ name: 'student-homework-kind', params: { kind: info.other } }" class="analysis__switch">
      查看{{ KIND_INFO[info.other].label }}分析
    </RouterLink>
    <RouterLink :to="{ name: 'student-homework-kind', params: { kind } }" class="btn btn--primary">返回</RouterLink>
  </PageHeader>

  <h2 class="compare__kind" :class="`compare__kind--${kind}`"><span aria-hidden="true">{{ info.icon }}</span> 練習對比</h2>
  <p v-if="error" class="error-text">{{ error }}</p>
  <p v-else-if="loaded && (!current || !previous)" class="card empty">要有上一次練習才能對比。</p>

  <template v-if="current && previous">
    <template v-if="kind === 'quiz'">
      <h3 class="compare__title">錯誤題目比較</h3>
      <div class="card compare__wrong">
        <div v-for="item in pair" :key="item.no" class="compare__round">
          <p class="muted">第 {{ item.no }} 次答錯題目（{{ dateOnly(item.submittedAt) }}）</p>
          <p v-if="!item.quiz?.wrong.length">全部答對</p>
          <div v-for="wrong in item.quiz?.wrong" :key="wrong.question_id" class="compare__question">
            <strong>第 {{ wrong.position }} 題<template v-if="wrong.topic">｜{{ wrong.topic }}</template></strong>
            <p>題目：{{ wrong.question }}</p>
          </div>
        </div>
      </div>
      <section class="compare__summary">
        <h3>練習進步摘要</h3>
        <ul>
          <li v-for="line in summary" :key="line">{{ line }}</li>
        </ul>
      </section>
    </template>

    <template v-else>
      <section v-for="item in pair" :key="item.no" class="compare__play">
        <h3 class="compare__title">第 {{ item.no }} 次練習（{{ dateOnly(item.submittedAt) }}）</h3>
        <ScoreCompare v-if="item.recording?.feedback?.has_score_sheet" :url="studentScoreSheetUrl(item.recording.id)" />
        <div v-if="item.recording" class="card">
          <FeedbackView :recording="item.recording" />
        </div>
      </section>
    </template>
  </template>
</template>

<style scoped>
.analysis__switch {
  align-self: center;
  color: var(--home-muted);
}

.analysis__switch:hover {
  color: var(--home-accent);
}

.compare__kind {
  margin: 0 0 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--home-line);
  font-size: 22px;
  font-weight: 500;
}

.compare__kind--performance {
  color: #3f8f2a;
}

.compare__kind--quiz {
  color: #1f66b8;
}

.compare__title {
  margin: 0 0 12px;
  font-size: 18px;
}

.compare__wrong {
  background: #f7f4f0;
}

.compare__round + .compare__round {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--home-line);
}

.compare__round > .muted {
  margin: 0 0 8px;
  font-size: 13px;
}

.compare__question + .compare__question {
  margin-top: 10px;
}

.compare__question p {
  margin: 2px 0 0;
  font-size: 14px;
}

.compare__summary {
  margin-top: 18px;
  padding: 14px 20px;
  border: 1px solid #9fc07a;
  border-radius: 20px;
  background: #e9eedf;
}

.compare__summary h3 {
  margin: 0 0 6px;
  color: #3f8f2a;
  font-size: 16px;
}

.compare__summary ul {
  margin: 0;
  padding-left: 20px;
}

.compare__play + .compare__play {
  margin-top: 26px;
}
</style>
