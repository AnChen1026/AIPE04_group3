import { computed, ref } from 'vue'
import { fetchAssignmentRecordings, fetchMyAssignments, fetchQuizAttempts } from '@/api/student'
import type { Assignment, QuizAttempt, Recording } from '@/types/api'

// 作業分析用：一份作業的每一次練習（第 1 次、第 2 次…）。
// 演奏作業是每次錄音（依繳交時間排序），題庫作業是每次作答。
export interface PracticeAttempt {
  no: number
  submittedAt: string
  recording?: Recording
  quiz?: QuizAttempt
}

export function useAssignmentAttempts(assignmentId: string) {
  const assignment = ref<Assignment | null>(null)
  const attempts = ref<PracticeAttempt[]>([])
  const error = ref('')
  const loaded = ref(false)

  async function load() {
    try {
      assignment.value = (await fetchMyAssignments()).find((item) => item.id === assignmentId) ?? null
      if (!assignment.value) {
        error.value = '找不到這份作業。'
        return
      }
      if (assignment.value.kind === 'quiz') {
        attempts.value = (await fetchQuizAttempts(assignmentId)).map((item) => ({
          no: item.attempt_no,
          submittedAt: item.submitted_at,
          quiz: item,
        }))
      } else {
        const recordings = [...(await fetchAssignmentRecordings(assignmentId))].sort((a, b) => a.submitted_at.localeCompare(b.submitted_at))
        attempts.value = recordings.map((item, index) => ({ no: index + 1, submittedAt: item.submitted_at, recording: item }))
      }
    } catch (problem) {
      error.value = problem instanceof Error ? problem.message : '讀不到練習紀錄。'
    } finally {
      loaded.value = true
    }
  }

  const heading = computed(() => (assignment.value ? `${assignment.value.course_title} - ${assignment.value.title}` : '作業分析'))

  return { assignment, attempts, error, loaded, load, heading }
}

export const KIND_INFO = {
  performance: { label: '演奏作業', hint: '音高 · 節奏 · 回饋', icon: '♪', other: 'quiz' },
  quiz: { label: '題庫作業', hint: '錯題 · 答案 · 解析', icon: '☰', other: 'performance' },
} as const

export type AnalysisKind = keyof typeof KIND_INFO
