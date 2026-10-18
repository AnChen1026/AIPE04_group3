<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { fetchMyStudents, fetchTeacherConversations, issueBindingCode, unbindStudent } from '@/api/teacher'
import type { BoundStudent, Conversation } from '@/types/api'
import { formatDate } from '@/utils/format'

const students = ref<BoundStudent[]>([])
const conversations = ref<Conversation[]>([])
const keyword = ref('')
const error = ref('')
const pendingUnbind = ref<{ student: BoundStudent; courseId: string; courseTitle: string } | null>(null)
const issuing = ref('')
const copied = ref('')

// 還在洽詢、沒有加入課程的學生。老師決定收學生時，在這裡（或聊天裡）發綁定碼
const inquiries = computed(() => conversations.value.filter((item) => !item.bound))

async function issue(conversation: Conversation) {
  issuing.value = conversation.id
  error.value = ''
  try {
    await issueBindingCode(conversation.id)
    await load()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '綁定碼沒有產生成功。'
  } finally {
    issuing.value = ''
  }
}

async function copy(code: string) {
  await navigator.clipboard?.writeText(code).catch(() => undefined)
  copied.value = code
  window.setTimeout(() => (copied.value = ''), 1600)
}

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

  <section v-if="inquiries.length" class="card inquiries">
    <h2 class="card__title">洽詢中、還沒加入的學生</h2>
    <p class="muted inquiries__hint">
      綁定碼只給這位學生的這門課。發出後也會貼進你們的聊天；學生可以在聊天或「我的課程」輸入。重發會讓舊碼失效。
    </p>
    <ul>
      <li v-for="item in inquiries" :key="item.id">
        <div class="inquiries__who">
          <strong>{{ item.student_name }}</strong>
          <span class="muted">{{ item.course_title }}</span>
        </div>
        <div class="inquiries__actions">
          <template v-if="item.binding_code">
            <code class="inquiries__code">{{ item.binding_code }}</code>
            <button type="button" class="btn btn--ghost btn--small" @click="copy(item.binding_code)">
              {{ copied === item.binding_code ? '已複製' : '複製' }}
            </button>
          </template>
          <button type="button" class="btn btn--primary btn--small" :disabled="issuing === item.id" @click="issue(item)">
            {{ item.binding_code ? '重發綁定碼' : '發綁定碼' }}
          </button>
          <RouterLink :to="`/teacher/chat/${item.id}`" class="btn btn--ghost btn--small">聊天</RouterLink>
        </div>
      </li>
    </ul>
  </section>

  <h2 class="students__title">已加入課程的學生</h2>
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

.inquiries {
  margin-bottom: 24px;
}

.inquiries__hint {
  margin: -4px 0 8px;
  font-size: 13px;
}

.inquiries ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.inquiries li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 12px 0;
  border-top: 1px solid var(--home-line);
}

.inquiries__who {
  display: flex;
  flex-direction: column;
}

.inquiries__who span {
  font-size: 13px;
}

.inquiries__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.inquiries__code {
  padding: 4px 12px;
  border-radius: 10px;
  background: var(--home-cream);
  color: var(--home-accent-dark);
  font-size: 15px;
  letter-spacing: 0.12em;
}

.students__title {
  margin: 0 0 12px;
  font-size: 17px;
  font-weight: 500;
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
