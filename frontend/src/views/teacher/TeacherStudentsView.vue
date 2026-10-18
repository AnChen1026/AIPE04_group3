<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { fetchMyStudents, fetchTeacherConversations, unbindStudent } from '@/api/teacher'
import type { BoundStudent, Conversation } from '@/types/api'
import { formatDate } from '@/utils/format'

const students = ref<BoundStudent[]>([])
const conversations = ref<Conversation[]>([])
const keyword = ref('')
const error = ref('')
const pendingUnbind = ref<{ student: BoundStudent; courseId: string; courseTitle: string } | null>(null)

const shown = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  if (!text) return students.value
  return students.value.filter((student) =>
    [student.name, student.email, ...student.courses.map((course) => course.course_title)].some((value) =>
      value.toLowerCase().includes(text),
    ),
  )
})

function conversationFor(studentId: string, courseId: string) {
  return conversations.value.find((item) => item.student_id === studentId && item.course_id === courseId)
}

async function load() {
  try {
    ;[students.value, conversations.value] = await Promise.all([fetchMyStudents(), fetchTeacherConversations()])
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到學生名單。'
  }
}

async function confirmUnbind() {
  if (!pendingUnbind.value) return
  const { student, courseId } = pendingUnbind.value
  pendingUnbind.value = null
  try {
    await unbindStudent(courseId, student.id)
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '解除綁定失敗。'
  }
  await load()
}

onMounted(load)
</script>

<template>
  <PageHeader title="學生管理" description="已用綁定碼進入你課程的學生。新的洽詢在「聊天」裡回覆並發綁定碼。">
    <label class="search-input">
      <span class="visually-hidden">搜尋學生</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋學生或課程" />
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
    </label>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="shown.length === 0" class="card empty">
    {{ students.length === 0 ? '還沒有學生綁定你的課程。' : '找不到符合的學生。' }}
  </div>
  <article v-for="student in shown" :key="student.id" class="card student">
    <div class="student__head">
      <span class="student__avatar" aria-hidden="true">{{ student.name.slice(0, 1) }}</span>
      <div>
        <strong>{{ student.name }}</strong>
        <p class="muted">{{ student.email }}</p>
      </div>
    </div>
    <ul class="student__courses">
      <li v-for="course in student.courses" :key="course.course_id">
        <div>
          <span>{{ course.course_title }}</span>
          <span class="muted">・{{ formatDate(course.bound_at) }} 綁定</span>
        </div>
        <div class="student__actions">
          <RouterLink
            v-if="conversationFor(student.id, course.course_id)"
            :to="`/teacher/chat/${conversationFor(student.id, course.course_id)!.id}`"
            class="btn btn--ghost btn--small"
          >
            聊天
          </RouterLink>
          <button
            type="button"
            class="btn btn--danger btn--small"
            @click="pendingUnbind = { student, courseId: course.course_id, courseTitle: course.course_title }"
          >
            解除綁定
          </button>
        </div>
      </li>
    </ul>
  </article>

  <NoticeDialog
    :open="pendingUnbind !== null"
    :message="`解除 ${pendingUnbind?.student.name ?? ''} 的綁定？`"
    :detail="`學生將不能再使用「${pendingUnbind?.courseTitle ?? ''}」的課表與練習，對話會保留。之後要重新上課，需要再發一組綁定碼。`"
    confirm-text="解除綁定"
    cancel-text="取消"
    danger
    @confirm="confirmUnbind"
    @cancel="pendingUnbind = null"
  />
</template>

<style scoped>
.search-input {
  width: min(260px, 100%);
}

.student__head {
  display: flex;
  align-items: center;
  gap: 14px;
}

.student__head p {
  margin: 2px 0 0;
  font-size: 13px;
}

.student__avatar {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--home-wood);
  color: var(--home-accent-dark);
  font-family: var(--font-serif);
  font-size: 18px;
}

.student__courses {
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.student__courses li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 0;
  border-top: 1px solid var(--home-line);
}

.student__actions {
  display: flex;
  gap: 8px;
}
</style>
