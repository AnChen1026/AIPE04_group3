<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import FeedbackView from '@/components/console/FeedbackView.vue'
import { fetchCourseRecordings, fetchMyCourses } from '@/api/teacher'
import { apiUrl } from '@/api/http'
import type { Course, TeacherRecording } from '@/types/api'
import { formatDateTime } from '@/utils/format'

// 設計稿的「作業管理」：學生照這門課的參考 MIDI 送出的練習錄音與每次的回饋
const courses = ref<Course[]>([])
const courseId = ref('')
const recordings = ref<TeacherRecording[]>([])
const studentFilter = ref('')
const error = ref('')
let timer = 0

const course = computed(() => courses.value.find((item) => item.id === courseId.value))
const students = computed(() => [...new Map(recordings.value.map((item) => [item.student_id, item.student_name])).entries()])
const shown = computed(() => recordings.value.filter((item) => !studentFilter.value || item.student_id === studentFilter.value))

async function loadRecordings() {
  window.clearTimeout(timer)
  if (!courseId.value) return
  try {
    recordings.value = await fetchCourseRecordings(courseId.value)
    error.value = ''
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到練習錄音。'
  }
  // 還有錄音在分析時，每 5 秒更新一次
  if (recordings.value.some((item) => item.status === 'pending' || item.status === 'processing')) {
    timer = window.setTimeout(loadRecordings, 5000)
  }
}

watch(courseId, () => {
  studentFilter.value = ''
  loadRecordings()
})

onMounted(async () => {
  courses.value = (await fetchMyCourses()).filter((item) => item.status !== 'archived')
  courseId.value = courses.value[0]?.id ?? ''
})

onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <PageHeader title="作業管理" description="學生照參考 MIDI 錄的練習，以及每一次的音高、節奏與文字回饋。">
    <select v-model="courseId" class="select practice__select" aria-label="選擇課程">
      <option v-if="courses.length === 0" value="">還沒有課程</option>
      <option v-for="item in courses" :key="item.id" :value="item.id">{{ item.title }}</option>
    </select>
    <select v-if="students.length > 1" v-model="studentFilter" class="select practice__select" aria-label="選擇學生">
      <option value="">全部學生</option>
      <option v-for="[id, name] in students" :key="id" :value="id">{{ name }}</option>
    </select>
  </PageHeader>

  <div v-if="course && !course.has_reference_midi" class="card practice__notice">
    這門課還沒有參考 MIDI，學生暫時不能送出練習。
    <RouterLink :to="`/teacher/courses/${course.id}/edit`">到課程設定上傳</RouterLink>
  </div>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="courseId && shown.length === 0" class="card empty">這門課還沒有學生送出練習。</div>
  <article v-for="item in shown" :key="item.id" class="card recording">
    <header class="recording__head">
      <strong>{{ item.student_name }}</strong>
      <span class="muted">{{ formatDateTime(item.submitted_at) }}</span>
    </header>
    <audio class="recording__audio" controls preload="none" :src="apiUrl(`/teacher/recordings/${item.id}/audio`)"></audio>
    <FeedbackView :recording="item" />
  </article>
</template>

<style scoped>
.practice__select {
  width: auto;
  min-width: 180px;
}

.practice__notice {
  margin-bottom: 16px;
  background: var(--home-cream);
  font-size: 14px;
}

.practice__notice a {
  margin-left: 6px;
  color: var(--home-accent);
  text-decoration: underline;
}

.recording__head {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.recording__audio {
  display: block;
  width: 100%;
  max-width: 420px;
  margin: 10px 0;
}
</style>
