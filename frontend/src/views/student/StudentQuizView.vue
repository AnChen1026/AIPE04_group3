<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import QuizQuestionCard from '@/components/console/QuizQuestionCard.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { fetchMyAssignments, fetchQuiz, submitQuiz } from '@/api/student'
import type { Assignment, QuizQuestion } from '@/types/api'

// 設計稿的學生「作業-題庫」：一次一題，可以看提示，上一題／下一題，最後「提交作業」。
// 交卷後直接到這次的「錯誤題目與解析」。
const route = useRoute()
const router = useRouter()
const assignmentId = String(route.params.id)
const assignment = ref<Assignment | null>(null)
const questions = ref<QuizQuestion[]>([])
const answers = reactive<Record<string, number[]>>({})
const index = ref(0)
const error = ref('')
const submitting = ref(false)
const confirming = ref(false)

const current = computed(() => questions.value[index.value])
const unanswered = computed(() => questions.value.filter((item) => !answers[item.id]?.length).map((item) => item.position))

function askSubmit() {
  error.value = ''
  if (unanswered.value.length) {
    error.value = `第 ${unanswered.value.join('、')} 題還沒作答。`
    index.value = (unanswered.value[0] ?? 1) - 1
    return
  }
  confirming.value = true
}

async function submit() {
  confirming.value = false
  submitting.value = true
  try {
    const attempt = await submitQuiz(
      assignmentId,
      questions.value.map((item) => ({ question_id: item.id, selected: answers[item.id] ?? [] })),
    )
    router.push({ name: 'student-analysis-detail', params: { kind: 'quiz', id: assignmentId, attempt: attempt.attempt_no } })
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '作業沒有送出。'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    ;[assignment.value, questions.value] = await Promise.all([
      fetchMyAssignments().then((items) => items.find((item) => item.id === assignmentId) ?? null),
      fetchQuiz(assignmentId),
    ])
    if (!assignment.value) error.value = '找不到這份作業。'
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到題目。'
  }
})
</script>

<template>
  <PageHeader :title="assignment ? `${assignment.title}｜單元測驗` : '題庫作業'">
    <RouterLink :to="{ name: 'student-homework-kind', params: { kind: 'quiz' } }" class="btn btn--primary">返回</RouterLink>
  </PageHeader>

  <div v-if="assignment" class="quiz">
    <p class="quiz__meta">
      <span>{{ assignment.course_title }}・{{ assignment.teacher_name }}老師</span>
      <span>共 {{ questions.length }} 題</span>
    </p>
    <QuizQuestionCard
      v-if="current"
      v-model:selected="answers[current.id]"
      mode="answer"
      :index="index"
      :total="questions.length"
      :type="current.question_type"
      :difficulty="current.difficulty"
      :topic="current.topic"
      :question="current.question"
      :options="current.options"
      :hint="current.hint"
      @prev="index--"
      @next="index++"
    />
    <p v-else class="card empty">這份作業還沒有題目。</p>

    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    <button v-if="questions.length" type="button" class="btn btn--primary btn--block quiz__submit" :disabled="submitting" @click="askSubmit">
      {{ submitting ? '送出中…' : '提交作業' }}
    </button>
  </div>
  <p v-else-if="error" class="error-text" role="alert">{{ error }}</p>

  <NoticeDialog
    :open="confirming"
    message="確定提交作業？"
    detail="交出後會看到答錯的題目與解析。之後還可以再練習一次。"
    confirm-text="提交"
    cancel-text="再檢查一下"
    @confirm="submit"
    @cancel="confirming = false"
  />
</template>

<style scoped>
.quiz {
  max-width: 720px;
}

.quiz__meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin: -8px 0 14px;
  color: var(--home-muted);
  font-size: 14px;
}

.quiz__submit {
  margin-top: 18px;
}
</style>
