<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import FeedbackView from '@/components/console/FeedbackView.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { deleteAssignment, fetchAssignments, fetchCourseRecordings, teacherAssignmentMidiUrl, teacherMaterialUrl } from '@/api/teacher'
import { apiUrl } from '@/api/http'
import type { Assignment, TeacherRecording } from '@/types/api'
import { ASSIGNMENT_KIND_LABELS, dueText, fileSizeText, formatDateTime } from '@/utils/format'

// 設計稿的「學生作業詳情」：這份作業給誰、內容與期限、附的檔案，以及學生每次繳交的錄音與回饋
const route = useRoute()
const router = useRouter()
const assignmentId = String(route.params.id)
const assignment = ref<Assignment | null>(null)
const recordings = ref<TeacherRecording[]>([])
const error = ref('')
const confirming = ref(false)
let timer = 0

const submitted = computed(() => recordings.value.length > 0)

async function load() {
  window.clearTimeout(timer)
  try {
    if (!assignment.value) {
      assignment.value = (await fetchAssignments()).find((item) => item.id === assignmentId) ?? null
      if (!assignment.value) {
        error.value = '找不到這份作業。'
        return
      }
    }
    recordings.value = (await fetchCourseRecordings(assignment.value.course_id)).filter((item) => item.assignment_id === assignmentId)
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到作業。'
  }
  // 還有錄音在分析時，每 5 秒更新一次
  if (recordings.value.some((item) => item.status === 'pending' || item.status === 'processing')) {
    timer = window.setTimeout(load, 5000)
  }
}

async function remove() {
  confirming.value = false
  try {
    await deleteAssignment(assignmentId)
    router.push('/teacher/practice')
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '作業沒有刪除。'
  }
}

onMounted(load)
onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <PageHeader title="學生作業詳情">
    <RouterLink to="/teacher/practice" class="btn btn--ghost">返回</RouterLink>
    <button v-if="assignment" type="button" class="btn btn--danger" @click="confirming = true">刪除作業</button>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <template v-if="assignment">
    <article class="tone-card detail">
      <p class="tone-card__cell tone-card__title detail__who">{{ assignment.student_name }}</p>
      <div class="tone-card__cell">
        <p class="tone-card__title">作業內容</p>
        <p class="tone-card__line">{{ assignment.title }}</p>
      </div>
      <div class="tone-card__cell">
        <p class="tone-card__title">
          {{ assignment.kind === 'quiz' ? '題庫作業' : submitted ? `學生已繳交 ${recordings.length} 次` : '作業尚未繳交' }}
        </p>
        <p class="tone-card__line">{{ dueText(assignment.due_at) }}</p>
      </div>
    </article>

    <section class="card files">
      <h2 class="card__title">{{ ASSIGNMENT_KIND_LABELS[assignment.kind] }}・{{ assignment.course_title }}</h2>
      <p v-if="assignment.description" class="files__note">{{ assignment.description }}</p>
      <ul class="files__list">
        <li v-if="assignment.has_midi">
          <span>參考 MIDI：{{ assignment.midi_filename }}</span>
          <a :href="teacherAssignmentMidiUrl(assignment.id)" class="btn btn--ghost btn--small">下載</a>
        </li>
        <li v-for="item in assignment.materials" :key="item.id">
          <span>教材：{{ item.filename }} <small class="muted">{{ fileSizeText(item.file_size_bytes) }}</small></span>
          <a :href="teacherMaterialUrl(item.id)" class="btn btn--ghost btn--small">下載</a>
        </li>
        <li v-if="!assignment.has_midi && assignment.materials.length === 0" class="muted">這份作業沒有附檔案。</li>
      </ul>
    </section>

    <section v-if="assignment.kind === 'performance'" class="card">
      <h2 class="card__title">繳交紀錄</h2>
      <p v-if="recordings.length === 0" class="muted">學生還沒有繳交。</p>
      <article v-for="item in recordings" :key="item.id" class="recording">
        <strong>{{ formatDateTime(item.submitted_at) }}</strong>
        <audio class="recording__audio" controls preload="none" :src="apiUrl(`/teacher/recordings/${item.id}/audio`)"></audio>
        <FeedbackView :recording="item" />
      </article>
    </section>
  </template>

  <NoticeDialog
    :open="confirming"
    message="刪除這份作業？"
    detail="參考 MIDI 與教材檔會一起刪除。學生已繳交的錄音與回饋會保留。"
    confirm-text="刪除"
    cancel-text="取消"
    danger
    @confirm="remove"
    @cancel="confirming = false"
  />
</template>

<style scoped>
.detail {
  grid-template-columns: 150px minmax(0, 1fr) minmax(0, 1.4fr);
  margin-bottom: 18px;
}

.detail__who {
  text-align: center;
}

.files__note {
  margin: -4px 0 10px;
  color: var(--home-muted);
  white-space: pre-wrap;
}

.files__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.files__list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-top: 1px solid var(--home-line);
}

.files__list li:first-child {
  border-top: 0;
}

.recording + .recording {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid var(--home-line);
}

.recording__audio {
  display: block;
  width: 100%;
  max-width: 420px;
  margin: 10px 0;
}

@media (max-width: 720px) {
  .detail__who {
    text-align: left;
  }
}
</style>
