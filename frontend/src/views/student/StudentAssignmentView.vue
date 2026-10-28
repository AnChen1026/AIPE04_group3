<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import AudioRecorder from '@/components/console/AudioRecorder.vue'
import FeedbackView from '@/components/console/FeedbackView.vue'
import ScoreCompare from '@/components/console/ScoreCompare.vue'
import {
  fetchAssignmentRecordings,
  fetchMyAssignments,
  studentAssignmentMidiUrl,
  studentMaterialUrl,
  studentScoreSheetUrl,
  submitAssignment,
} from '@/api/student'
import { apiUrl } from '@/api/http'
import type { Assignment, Recording } from '@/types/api'
import { ASSIGNMENT_KIND_LABELS, dueText, fileSizeText, formatDateTime } from '@/utils/format'

// 一份作業：下載老師給的參考 MIDI 與教材，演奏作業錄音繳交後會收到音高、節奏與文字回饋
const route = useRoute()
const assignmentId = String(route.params.id)
const assignment = ref<Assignment | null>(null)
const recordings = ref<Recording[]>([])
const recorder = ref<InstanceType<typeof AudioRecorder> | null>(null)
const uploading = ref(false)
const error = ref('')
const notice = ref('')
// 正在看哪一筆的對照樂譜
const openSheet = ref('')
let timer = 0

async function loadRecordings() {
  window.clearTimeout(timer)
  try {
    recordings.value = await fetchAssignmentRecordings(assignmentId)
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到繳交紀錄。'
  }
  // 分析還沒完成時每 4 秒看一次
  if (recordings.value.some((item) => item.status === 'pending' || item.status === 'processing')) {
    timer = window.setTimeout(loadRecordings, 4000)
  }
}

async function submit(audio: Blob, filename: string, metronomeBpm: number | null) {
  error.value = ''
  notice.value = ''
  uploading.value = true
  try {
    await submitAssignment(assignmentId, audio, filename, metronomeBpm)
    recorder.value?.discard()
    notice.value = '已繳交，分析大約需要半分鐘。'
    await loadRecordings()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '錄音沒有送出。'
  } finally {
    uploading.value = false
  }
}

onMounted(async () => {
  try {
    assignment.value = (await fetchMyAssignments()).find((item) => item.id === assignmentId) ?? null
    if (!assignment.value) {
      error.value = '找不到這份作業。'
      return
    }
    if (assignment.value.kind === 'performance') await loadRecordings()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到作業。'
  }
  // 從作業列表的「查看詳情」進來（#history）時，捲到繳交紀錄
  if (route.hash) {
    await nextTick()
    document.querySelector(route.hash)?.scrollIntoView({ behavior: 'smooth' })
  }
})

onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <PageHeader :title="(assignment && ASSIGNMENT_KIND_LABELS[assignment.kind]) || '作業'">
    <RouterLink to="/student/homework" class="btn btn--ghost">返回</RouterLink>
  </PageHeader>
  <p v-if="error" class="error-text" role="alert">{{ error }}</p>

  <template v-if="assignment">
    <section class="card">
      <h2 class="card__title">{{ assignment.title }}</h2>
      <p class="muted info">{{ assignment.course_title }}・{{ dueText(assignment.due_at) }}</p>
      <p v-if="assignment.description" class="info__note">{{ assignment.description }}</p>
      <ul class="files">
        <li v-if="assignment.has_midi">
          <span>參考曲：{{ assignment.midi_filename }}</span>
          <a :href="studentAssignmentMidiUrl(assignment.id)" class="btn btn--ghost btn--small">下載 MIDI</a>
        </li>
        <li v-for="item in assignment.materials" :key="item.id">
          <span>教材：{{ item.filename }} <small class="muted">{{ fileSizeText(item.file_size_bytes) }}</small></span>
          <a :href="studentMaterialUrl(item.id)" class="btn btn--ghost btn--small">下載</a>
        </li>
      </ul>
    </section>

    <template v-if="assignment.kind === 'performance'">
      <section class="card">
        <h2 class="card__title">錄音繳交</h2>
        <p class="muted info">照參考曲錄一段，系統會分開看音高和節奏，給這一次的文字回饋，也會把你彈的轉成樂譜，和答案上下對照。</p>
        <AudioRecorder
          ref="recorder"
          :busy="uploading"
          :default-bpm="assignment.practice_bpm ?? assignment.midi_bpm ?? 120"
          @submit="submit"
        />
        <p v-if="notice" class="notice" role="status">{{ notice }}</p>
      </section>

      <section id="history" class="card">
        <h2 class="card__title">繳交紀錄</h2>
        <p v-if="recordings.length === 0" class="muted">還沒有繳交過。</p>
        <article v-for="item in recordings" :key="item.id" class="history">
          <header>
            <strong>{{ formatDateTime(item.submitted_at) }}</strong>
            <span v-if="item.metronome_bpm" class="badge badge--soft">節拍器 {{ Math.round(item.metronome_bpm) }} BPM</span>
            <audio controls preload="none" :src="apiUrl(`/api/student/recordings/${item.id}/audio`)"></audio>
            <button
              v-if="item.feedback?.has_score_sheet"
              type="button"
              class="btn btn--ghost btn--small"
              :aria-expanded="openSheet === item.id"
              @click="openSheet = openSheet === item.id ? '' : item.id"
            >
              {{ openSheet === item.id ? '收起對照譜' : '看對照譜' }}
            </button>
          </header>
          <FeedbackView :recording="item" />
          <ScoreCompare v-if="openSheet === item.id" :url="studentScoreSheetUrl(item.id)" />
        </article>
      </section>
    </template>

    <section v-else class="card">
      <h2 class="card__title">作答</h2>
      <p class="muted">題庫作答尚未開放，先下載上面的教材練習。</p>
    </section>
  </template>
</template>

<style scoped>
.info {
  margin: -6px 0 12px;
  font-size: 14px;
}

.info__note {
  margin: 0 0 12px;
  white-space: pre-wrap;
}

.files {
  margin: 0;
  padding: 0;
  list-style: none;
}

.files li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-top: 1px solid var(--home-line);
}

.notice {
  margin: 12px 0 0;
  color: var(--home-accent-dark);
  font-size: 14px;
}

.history {
  padding: 16px 0;
  border-top: 1px solid var(--home-line);
}

.history:first-of-type {
  border-top: 0;
}

.history header {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
</style>
