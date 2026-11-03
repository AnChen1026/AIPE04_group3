<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import ConsoleIcon from '@/components/console/ConsoleIcon.vue'
import { fetchMyChangeRequests, fetchStudentSchedule } from '@/api/student'
import { useBoundCourses } from '@/composables/useBoundCourses'
import type { ChangeRequest, Lesson } from '@/types/api'
import { sameDay } from '@/utils/format'

// 學生的資訊總覽：今天的課、等老師確認的申請、還沒看的訊息
const courses = useBoundCourses()
const lessons = ref<Lesson[]>([])
const requests = ref<ChangeRequest[]>([])
const loading = ref(true)
const error = ref('')

const today = new Date()
const todayLessons = computed(() =>
  lessons.value.filter((lesson) => lesson.status === 'scheduled' && sameDay(new Date(lesson.starts_at), today)),
)
const pending = computed(() => requests.value.filter((item) => item.status === 'pending'))
const leaveCount = computed(() => pending.value.filter((item) => item.request_type === 'leave').length)
const bookingCount = computed(() => pending.value.length - leaveCount.value)
const unreadCount = computed(() => courses.conversations.value.filter((item) => item.unread_count > 0).length)

onMounted(async () => {
  try {
    await courses.load()
    const ids = courses.bound.value.map((item) => item.course_id)
    const [lessonLists, requestLists] = await Promise.all([
      Promise.all(ids.map(fetchStudentSchedule)),
      Promise.all(ids.map(fetchMyChangeRequests)),
    ])
    lessons.value = lessonLists.flat()
    requests.value = requestLists.flat()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到資料。'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <PageHeader title="資訊總覽" />
  <p v-if="error" class="error-text">{{ error }}</p>

  <div class="stats">
    <RouterLink to="/student/schedule" class="card stat">
      <span class="stat__label"><ConsoleIcon name="calendar" />今日課程</span>
      <strong>{{ loading ? '—' : todayLessons.length }}<small>堂</small></strong>
    </RouterLink>
    <RouterLink to="/student/schedule" class="card stat">
      <span class="stat__label"><ConsoleIcon name="users" />待老師確認申請</span>
      <strong>{{ loading ? '—' : pending.length }}<small>筆</small></strong>
    </RouterLink>
  </div>

  <section class="card">
    <h2 class="card__title"><ConsoleIcon name="clipboard" />待處理事項</h2>
    <ul v-if="!loading" class="todo">
      <li v-if="leaveCount"><RouterLink to="/student/schedule">{{ leaveCount }} 筆請假申請待老師確認</RouterLink></li>
      <li v-if="bookingCount"><RouterLink to="/student/schedule">{{ bookingCount }} 筆約課／調課申請待老師確認</RouterLink></li>
      <li v-if="unreadCount"><RouterLink to="/student/chat">{{ unreadCount }} 位老師傳了新訊息</RouterLink></li>
      <li v-if="courses.bound.value.length === 0">
        <RouterLink to="/student/teachers">還沒有加入課程，輸入老師給的綁定碼</RouterLink>
      </li>
      <li v-if="!leaveCount && !bookingCount && !unreadCount && courses.bound.value.length" class="muted">目前沒有待處理的事。</li>
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

.stat__label svg,
.card__title svg {
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

.todo {
  margin: 0;
  padding-left: 20px;
  line-height: 2;
}

.todo a:hover {
  color: var(--home-accent);
}

@media (max-width: 640px) {
  .stats {
    grid-template-columns: 1fr;
  }
}
</style>
