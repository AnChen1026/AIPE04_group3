<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import FeedbackView from '@/components/console/FeedbackView.vue'
import ScoreCompare from '@/components/console/ScoreCompare.vue'
import QuizWrongList from '@/components/console/QuizWrongList.vue'
import { studentScoreSheetUrl } from '@/api/student'
import { KIND_INFO, useAssignmentAttempts, type AnalysisKind } from '@/composables/useAssignmentAttempts'
import { dateOnly } from '@/utils/format'

// 設計稿「作業分析-單次演奏詳情／單次題庫詳情」：
// 演奏作業看樂譜比對結果與回饋；題庫作業看錯誤題目、學生作答、正確答案與解析
const route = useRoute()
const kind = computed(() => (route.params.kind === 'quiz' ? 'quiz' : 'performance') as AnalysisKind)
const info = computed(() => KIND_INFO[kind.value])
const assignmentId = String(route.params.id)
const attemptNo = Number(route.params.attempt)
const { assignment, attempts, error, loaded, load, heading } = useAssignmentAttempts(assignmentId)
const attempt = computed(() => attempts.value.find((item) => item.no === attemptNo) ?? null)
let timer = 0

async function refresh() {
  await load()
  // 演奏作業還在分析時，每 4 秒看一次
  const status = attempt.value?.recording?.status
  if (status === 'pending' || status === 'processing') timer = window.setTimeout(refresh, 4000)
}

onMounted(refresh)
onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <PageHeader :title="heading">
    <RouterLink :to="{ name: 'student-analysis-list', params: { kind: info.other } }" class="analysis__switch">
      查看{{ KIND_INFO[info.other].label }}分析
    </RouterLink>
    <RouterLink :to="{ name: 'student-analysis-attempts', params: { kind, id: assignmentId } }" class="btn btn--primary">返回</RouterLink>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>
  <p v-else-if="loaded && !attempt" class="card empty">找不到第 {{ attemptNo }} 次練習。</p>

  <template v-if="assignment && attempt">
    <p class="meta">
      <span>學生：{{ assignment.student_name }}</span>
      <span>作業繳交日期：{{ dateOnly(attempt.submittedAt) }}</span>
      <span>第 {{ attempt.no }} 次練習</span>
    </p>

    <template v-if="attempt.recording">
      <section class="block">
        <h2 class="block__title">樂譜比對結果</h2>
        <ScoreCompare v-if="attempt.recording.feedback?.has_score_sheet" :url="studentScoreSheetUrl(attempt.recording.id)" />
        <p v-else class="card empty">
          {{ attempt.recording.status === 'completed' ? '這次沒有產生對照樂譜。' : '分析完成後會顯示對照樂譜。' }}
        </p>
      </section>
      <section class="block">
        <h2 class="block__title">回饋</h2>
        <div class="card">
          <FeedbackView :recording="attempt.recording" />
        </div>
      </section>
    </template>

    <section v-else-if="attempt.quiz" class="block">
      <h2 class="block__title">錯誤題目與解析</h2>
      <QuizWrongList :items="attempt.quiz.wrong" />
    </section>
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

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 18px;
  margin: -10px 0 18px;
  color: var(--home-muted);
  font-size: 14px;
}

.meta span + span {
  padding-left: 18px;
  border-left: 1px solid var(--home-line);
}

.block + .block {
  margin-top: 22px;
}

.block__title {
  margin: 0 0 12px;
  font-size: 18px;
}
</style>
