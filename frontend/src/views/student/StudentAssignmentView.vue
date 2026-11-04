<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import FeedbackView from '@/components/console/FeedbackView.vue'
import ScoreCompare from '@/components/console/ScoreCompare.vue'
import RecordDialog from '@/components/console/RecordDialog.vue'
import { fetchAssignmentRecordings, fetchMyAssignments, studentScoreSheetUrl, submitAssignment } from '@/api/student'
import { apiUrl } from '@/api/http'
import type { Assignment, Recording } from '@/types/api'
import { dueText, fileSizeText, formatDateTime } from '@/utils/format'

// 設計稿的學生「作業管理」：演奏作業上傳。課程、老師、上傳作業（選擇檔案或錄製音檔），按「儲存」繳交。
// 繳交後在下面的繳交紀錄看回饋與對照樂譜，也可以到「作業分析」看每次練習。
const route = useRoute()
const router = useRouter()
const assignmentId = String(route.params.id)
const assignment = ref<Assignment | null>(null)
const recordings = ref<Recording[]>([])
const take = ref<{ audio: Blob; filename: string } | null>(null)
const recording = ref(false)
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

function onFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (file.size > 20 * 1024 * 1024) {
    error.value = '音檔最大 20 MB。'
    return
  }
  error.value = ''
  take.value = { audio: file, filename: file.name }
}

function onRecorded(audio: Blob, filename: string) {
  take.value = { audio, filename: `錄音-${new Date().toLocaleTimeString('zh-TW', { hour12: false })}${filename.slice(filename.lastIndexOf('.'))}` }
  recording.value = false
}

async function save() {
  error.value = ''
  notice.value = ''
  if (!take.value) {
    error.value = '請先選擇音檔或錄製音檔。'
    return
  }
  uploading.value = true
  try {
    await submitAssignment(assignmentId, take.value.audio, take.value.filename)
    take.value = null
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
    if (assignment.value.kind === 'quiz') {
      router.replace({ name: 'student-quiz', params: { id: assignmentId } })
      return
    }
    await loadRecordings()
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
  <PageHeader title="作業管理">
    <RouterLink to="/student/homework" class="btn btn--ghost">返回</RouterLink>
    <button type="button" class="btn btn--primary" :disabled="uploading || !assignment" @click="save">{{ uploading ? '繳交中…' : '儲存' }}</button>
  </PageHeader>

  <div class="chip-group upload__tabs">
    <span class="chip" aria-pressed="true">演奏作業上傳</span>
  </div>
  <p v-if="error" class="error-text" role="alert">{{ error }}</p>

  <template v-if="assignment">
    <div class="upload">
      <div class="field">
        <span class="field__label">課程名稱</span>
        <p class="readonly">{{ assignment.course_title }}</p>
      </div>
      <div class="field">
        <span class="field__label">老師名稱</span>
        <p class="readonly">{{ assignment.teacher_name }}老師</p>
      </div>
      <div class="field">
        <span class="field__label">作業內容</span>
        <p class="readonly">{{ assignment.title }}<span class="muted">・{{ dueText(assignment.due_at) }}</span></p>
        <p v-if="assignment.description" class="note">{{ assignment.description }}</p>
      </div>
      <div class="field">
        <span class="field__label">上傳作業</span>
        <div class="file-row">
          <span class="file-row__name" :class="{ 'file-row__name--set': take }">
            {{ take ? `${take.filename}（${fileSizeText(take.audio.size)}）` : '照老師的作業彈一次，錄音或選一個音檔' }}
          </span>
          <button v-if="take" type="button" class="file-row__action" @click="take = null">移除</button>
        </div>
        <div class="file-row__links">
          <label class="file-row__action">
            選擇檔案
            <input type="file" accept="audio/*,.wav,.mp3,.m4a,.ogg,.webm" class="visually-hidden" @change="onFile" />
          </label>
          <button type="button" class="file-row__action" @click="recording = true">錄製音檔</button>
        </div>
        <p v-if="notice" class="notice" role="status">{{ notice }}</p>
      </div>
    </div>

    <section id="history" class="card">
      <h2 class="card__title">繳交紀錄</h2>
      <p v-if="recordings.length === 0" class="muted">還沒有繳交過。</p>
      <article v-for="item in recordings" :key="item.id" class="history">
        <header>
          <strong>{{ formatDateTime(item.submitted_at) }}</strong>
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

  <RecordDialog :open="recording" hint="錄好後按「確認送出」放進上傳作業，再按右上角「儲存」繳交" @close="recording = false" @done="onRecorded" />
</template>

<style scoped>
.upload__tabs {
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 2px solid var(--home-line);
}

.upload {
  max-width: 720px;
  margin-bottom: 22px;
}

.readonly {
  margin: 0;
  min-height: 42px;
  padding: 10px 16px;
  border: 1px solid var(--home-line);
  border-radius: var(--radius-pill);
  background: #fff;
}

.note {
  margin: 8px 0 0;
  padding: 0 16px;
  color: var(--home-muted);
  font-size: 14px;
  white-space: pre-wrap;
}

.file-row {
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 42px;
  padding: 0 16px;
  border: 1px solid var(--home-line);
  border-radius: var(--radius-pill);
  background: #fff;
}

.file-row__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: var(--home-muted);
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-row__name--set {
  color: var(--home-ink);
}

.file-row__links {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 6px;
}

.file-row__action {
  padding: 0;
  border: 0;
  background: none;
  color: var(--home-accent);
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

.file-row__action:hover {
  text-decoration: underline;
}

.notice {
  margin: 10px 0 0;
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
