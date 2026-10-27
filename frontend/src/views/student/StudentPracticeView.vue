<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import CoursePicker from '@/components/console/CoursePicker.vue'
import AudioRecorder from '@/components/console/AudioRecorder.vue'
import FeedbackView from '@/components/console/FeedbackView.vue'
import { fetchMyRecordings, uploadRecording } from '@/api/student'
import { apiUrl } from '@/api/http'
import { useBoundCourses } from '@/composables/useBoundCourses'
import type { Recording } from '@/types/api'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const courses = useBoundCourses()
const recordings = ref<Recording[]>([])
const recorder = ref<InstanceType<typeof AudioRecorder> | null>(null)
const uploading = ref(false)
const error = ref('')
const notice = ref('')
let timer = 0

async function load() {
  window.clearTimeout(timer)
  if (!courses.courseId.value) return
  try {
    recordings.value = await fetchMyRecordings(courses.courseId.value)
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到練習紀錄。'
  }
  // 分析還沒完成時每 4 秒看一次
  if (recordings.value.some((item) => item.status === 'pending' || item.status === 'processing')) {
    timer = window.setTimeout(load, 4000)
  }
}

async function submit(audio: Blob, filename: string) {
  error.value = ''
  notice.value = ''
  uploading.value = true
  try {
    await uploadRecording(courses.courseId.value, audio, filename)
    recorder.value?.discard()
    notice.value = '已送出，分析大約需要半分鐘。'
    await load()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '錄音沒有送出。'
  } finally {
    uploading.value = false
  }
}

watch(
  () => courses.courseId.value,
  () => {
    notice.value = ''
    load()
  },
)

onMounted(async () => {
  await courses.load()
  await load()
  // 從作業頁的「查看詳情」進來（#history）時，捲到繳交紀錄
  if (route.hash) {
    await nextTick()
    document.querySelector(route.hash)?.scrollIntoView({ behavior: 'smooth' })
  }
})

onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <PageHeader title="演奏作業" description="照老師指定的曲子錄一段，系統會分開看音高和節奏，並給這一次的文字回饋。">
    <CoursePicker v-model="courses.courseId.value" :courses="courses.bound.value" />
    <RouterLink to="/student/homework" class="btn btn--ghost">返回</RouterLink>
  </PageHeader>

  <div v-if="courses.loaded.value && courses.bound.value.length === 0" class="card empty">
    還沒有進入任何課程。在「老師」頁輸入老師給的綁定碼後，就能在這裡錄音交作業。
  </div>

  <template v-else-if="courses.courseId.value">
    <section class="card">
      <h2 class="card__title">這次的練習</h2>
      <p class="practice__reference">
        老師指定的參考曲：
        <a :href="apiUrl(`/api/student/courses/${courses.courseId.value}/reference-midi`)">下載 MIDI</a>
        <span class="muted">（如果老師還沒設定，會先無法送出錄音）</span>
      </p>
      <AudioRecorder ref="recorder" :busy="uploading" @submit="submit" />
      <p v-if="notice" class="practice__notice" role="status">{{ notice }}</p>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </section>

    <section id="history" class="card">
      <h2 class="card__title">繳交紀錄</h2>
      <p v-if="recordings.length === 0" class="muted">還沒有送出過練習。</p>
      <article v-for="item in recordings" :key="item.id" class="practice__item">
        <header>
          <strong>{{ formatDateTime(item.submitted_at) }}</strong>
          <audio controls preload="none" :src="apiUrl(`/api/student/recordings/${item.id}/audio`)"></audio>
        </header>
        <FeedbackView :recording="item" />
      </article>
    </section>
  </template>
</template>

<style scoped>
.practice__reference {
  margin: 0 0 16px;
  font-size: 14px;
}

.practice__reference a {
  color: var(--home-accent);
  text-decoration: underline;
}

.practice__notice {
  margin: 12px 0 0;
  color: var(--home-accent-dark);
  font-size: 14px;
}

.practice__item {
  padding: 16px 0;
  border-top: 1px solid var(--home-line);
}

.practice__item:first-of-type {
  border-top: 0;
}

.practice__item header {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.practice__item audio {
  height: 36px;
}
</style>
