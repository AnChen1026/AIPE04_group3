<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import ConsoleIcon from '@/components/console/ConsoleIcon.vue'
import { fetchChangeRequests, fetchMyLessons, fetchStudio, fetchTeacherConversations } from '@/api/teacher'
import type { Conversation, TeacherChangeRequest, TeacherLesson } from '@/types/api'
import { formatTime, sameDay } from '@/utils/format'

const lessons = ref<TeacherLesson[]>([])
const requests = ref<TeacherChangeRequest[]>([])
const conversations = ref<Conversation[]>([])
const loading = ref(true)
// 審核通過後還沒填工作室資料時，待處理事項的第一項提醒去建立
const hasStudio = ref(true)
const error = ref('')

const today = new Date()
const todayLessons = computed(() =>
  lessons.value.filter((lesson) => lesson.status === 'scheduled' && sameDay(new Date(lesson.starts_at), today)),
)
const leaveCount = computed(() => requests.value.filter((item) => item.request_type === 'leave').length)
const bookingCount = computed(() => requests.value.filter((item) => item.request_type !== 'leave').length)
const unreadConversations = computed(() => conversations.value.filter((item) => item.unread_count > 0))
const newInquiries = computed(() => conversations.value.filter((item) => !item.bound).length)

onMounted(async () => {
  try {
    let studio
    ;[lessons.value, requests.value, conversations.value, studio] = await Promise.all([
      fetchMyLessons(),
      fetchChangeRequests(),
      fetchTeacherConversations(),
      fetchStudio().catch(() => undefined),
    ])
    hasStudio.value = studio !== null
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到後台資料。'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <PageHeader title="資訊總覽" description="今天的課、待確認的申請和還沒回的訊息。" />
  <p v-if="error" class="error-text">{{ error }}</p>

  <div class="stats">
    <RouterLink to="/teacher/schedule" class="card stat">
      <span class="stat__label"><ConsoleIcon name="calendar" />今日課程</span>
      <strong>{{ loading ? '—' : todayLessons.length }}<small>堂</small></strong>
    </RouterLink>
    <RouterLink to="/teacher/schedule" class="card stat">
      <span class="stat__label"><ConsoleIcon name="users" />待確認預約</span>
      <strong>{{ loading ? '—' : requests.length }}<small>筆</small></strong>
    </RouterLink>
  </div>

  <section class="card">
    <h2 class="card__title"><ConsoleIcon name="clipboard" />待處理事項</h2>
    <ul v-if="!loading" class="todo">
      <li v-if="!hasStudio"><RouterLink to="/teacher/studio">還沒建立工作室資料，先去填寫</RouterLink></li>
      <li v-if="leaveCount"><RouterLink to="/teacher/schedule">{{ leaveCount }} 筆請假申請</RouterLink></li>
      <li v-if="bookingCount"><RouterLink to="/teacher/schedule">{{ bookingCount }} 筆約課／調課申請待確認</RouterLink></li>
      <li v-if="unreadConversations.length">
        <RouterLink to="/teacher/chat">{{ unreadConversations.length }} 則聊天訊息未回覆</RouterLink>
      </li>
      <li v-if="newInquiries"><RouterLink to="/teacher/chat">{{ newInquiries }} 位學生洽詢中、尚未綁定</RouterLink></li>
      <li v-if="hasStudio && !leaveCount && !bookingCount && !unreadConversations.length && !newInquiries" class="muted">目前沒有待處理的事。</li>
    </ul>
  </section>

  <section class="card">
    <h2 class="card__title"><ConsoleIcon name="schedule" />今天的課</h2>
    <p v-if="!loading && todayLessons.length === 0" class="muted">今天沒有排課。</p>
    <ul class="today">
      <li v-for="lesson in todayLessons" :key="lesson.id">
        <span class="today__time">{{ formatTime(lesson.starts_at) }}－{{ formatTime(lesson.ends_at) }}</span>
        <span>{{ lesson.course_title }}｜{{ lesson.student_name }}</span>
        <RouterLink :to="{ name: 'teacher-schedule', query: { summary: lesson.id } }" class="btn btn--ghost btn--small">課前摘要</RouterLink>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stats .card + .card {
  margin-top: 0;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color 0.2s ease;
}

.stat:hover {
  border-color: var(--home-wood);
}

.stat__label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--home-muted);
  font-size: 14px;
}

.stat__label svg {
  color: var(--home-accent);
}

.stat strong {
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: 40px;
  font-weight: 600;
  text-align: center;
}

.stat small {
  margin-left: 4px;
  font-family: var(--font-sans);
  font-size: 16px;
  font-weight: 400;
}

.card__title svg {
  color: var(--home-accent);
}

.todo {
  margin: 0;
  padding-left: 20px;
  line-height: 2;
}

.todo a:hover {
  color: var(--home-accent);
}

.today {
  margin: 0;
  padding: 0;
  list-style: none;
}

.today li {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 0;
  border-top: 1px solid var(--home-line);
}

.today li:first-child {
  border-top: 0;
}

.today__time {
  min-width: 110px;
  color: var(--home-accent);
  font-variant-numeric: tabular-nums;
}

.today .btn {
  margin-left: auto;
}

@media (max-width: 640px) {
  .stats {
    grid-template-columns: 1fr;
  }

  .today li {
    flex-wrap: wrap;
    gap: 6px 12px;
  }
}
</style>
