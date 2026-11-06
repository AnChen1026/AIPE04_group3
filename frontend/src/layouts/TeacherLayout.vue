<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ConsoleShell, { type NavItem } from '@/components/console/ConsoleShell.vue'
import TeacherApplicationForm from '@/components/console/TeacherApplicationForm.vue'
import { fetchChangeRequests, fetchQuizJobs, fetchTeacherConversations } from '@/api/teacher'
import { fetchCurrentUser } from '@/api/auth'
import { fetchSupportConversation } from '@/api/support'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const unread = ref(0)
const pending = ref(0)
// AI 出題：出好等老師審查的數量（作業選單的數字），以及剛出好的那一筆（右下角通知）
const quizReady = ref(0)
const finished = ref<{ id: string; title: string; ok: boolean } | null>(null)
let activeJobs = new Set<string>()
let quizTimer = 0

// 老師帳號要管理員核准後才能用後台；審核中或沒通過時只顯示狀態
const approved = computed(() => auth.user?.is_active === true)
const status = computed(() => auth.user?.application_status)

// 補填申請後重新讀一次登入資料，畫面換成「審核中」
async function onApplied() {
  auth.setUser(await fetchCurrentUser())
}

// 選單照設計稿：資訊總覽改成點最上方的老師姓名；工作室管理與設定維持原本的頁面
const items = computed<NavItem[]>(() => [
  { to: '/teacher/schedule', label: '課表', icon: 'schedule', badge: pending.value },
  { to: '/teacher/students', label: '學生', icon: 'students' },
  { to: '/teacher/courses', label: '課程', icon: 'courses' },
  { to: '/teacher/practice', label: '作業', icon: 'practice', badge: quizReady.value },
  { to: '/teacher/chat', label: '聊天', icon: 'chat', badge: unread.value },
  { to: '/teacher/studio', label: '工作室管理', icon: 'studio' },
  { to: '/teacher/settings', label: '設定', icon: 'settings' },
])

// 換頁時更新選單上的未讀與待處理數字
async function refreshBadges() {
  if (!approved.value) return
  const [conversations, requests, support] = await Promise.allSettled([
    fetchTeacherConversations(),
    fetchChangeRequests(),
    fetchSupportConversation(),
  ])
  const supportUnread = support.status === 'fulfilled' ? support.value.unread_count : 0
  if (conversations.status === 'fulfilled') {
    unread.value = conversations.value.reduce((sum, row) => sum + row.unread_count, 0) + supportUnread
  }
  if (requests.status === 'fulfilled') pending.value = requests.value.length
}

// 背景出題：每次換頁看一次；有出題中的就每 20 秒看一次，出好時跳通知
async function refreshQuizJobs() {
  window.clearTimeout(quizTimer)
  if (!approved.value) return
  try {
    const jobs = await fetchQuizJobs()
    quizReady.value = jobs.filter((job) => job.status === 'succeeded').length
    for (const job of jobs) {
      if (activeJobs.has(job.id) && (job.status === 'succeeded' || job.status === 'failed')) {
        finished.value = { id: job.id, title: job.title || job.source_filename, ok: job.status === 'succeeded' }
      }
    }
    activeJobs = new Set(jobs.filter((job) => job.status === 'queued' || job.status === 'running').map((job) => job.id))
  } catch {
    return
  }
  if (activeJobs.size) quizTimer = window.setTimeout(refreshQuizJobs, 20000)
}

watch(() => route.fullPath, refreshBadges, { immediate: true })
watch(() => route.fullPath, refreshQuizJobs, { immediate: true })
// 作業頁送出或重新出題時，馬上開始追蹤
window.addEventListener('quiz-jobs-changed', refreshQuizJobs)
onBeforeUnmount(() => {
  window.clearTimeout(quizTimer)
  window.removeEventListener('quiz-jobs-changed', refreshQuizJobs)
})
</script>

<template>
  <ConsoleShell heading="教師管理後台" :items="items" home-to="/teacher" role-label="老師" :top-actions="false">
    <RouterView v-if="approved" />
    <TeacherApplicationForm v-else-if="!status" @submitted="onApplied" />
    <div v-else class="card pending">
      <h1>{{ status === 'rejected' ? '老師申請沒有通過' : '老師申請審核中' }}</h1>
      <p v-if="status === 'rejected'">
        這次的申請沒有通過。如果想補充資料再申請，請聯絡平台管理員。
      </p>
      <p v-else>平台管理員確認你的資料後，就能開始建立課程、回覆學生洽詢。審核通過後重新整理這一頁即可。</p>
    </div>
    <div v-if="finished" class="quiz-toast" role="status">
      <p>
        <strong>{{ finished.ok ? 'AI 出題完成' : 'AI 出題失敗' }}</strong>
        「{{ finished.title }}」{{ finished.ok ? '可以審查了。' : '沒有出成功，可以在出題紀錄看原因。' }}
      </p>
      <RouterLink
        :to="finished.ok ? { name: 'teacher-assignment-new', query: { job: finished.id } } : { name: 'teacher-assignment-new', query: { tab: 'quiz' } }"
        class="btn btn--primary btn--small"
        @click="finished = null"
      >
        {{ finished.ok ? '審查題目' : '查看' }}
      </RouterLink>
      <button type="button" class="quiz-toast__close" aria-label="關閉通知" @click="finished = null">×</button>
    </div>
  </ConsoleShell>
</template>

<style scoped>
.quiz-toast {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 40;
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: min(420px, calc(100vw - 32px));
  padding: 14px 16px;
  border: 1px solid var(--home-accent);
  border-radius: 18px;
  background: var(--home-paper);
  box-shadow: 0 12px 32px rgba(62, 52, 44, 0.18);
  font-size: 14px;
}

.quiz-toast p {
  margin: 0;
  line-height: 1.6;
}

.quiz-toast__close {
  align-self: flex-start;
  padding: 0 4px;
  border: 0;
  background: none;
  color: var(--home-muted);
  font-size: 18px;
  cursor: pointer;
}

@media (max-width: 640px) {
  .quiz-toast {
    right: 16px;
    left: 16px;
    bottom: 16px;
  }
}

.pending h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 500;
}

.pending p {
  margin: 10px 0 0;
  color: var(--home-muted);
  line-height: 1.8;
}
</style>
