<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import AudioRecorder from '@/components/console/AudioRecorder.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { createAssignment, fetchMyCourses, fetchMyStudents } from '@/api/teacher'
import type { Assignment, BoundStudent, Course } from '@/types/api'
import { fileSizeText } from '@/utils/format'

// 設計稿的「作業管理」：演奏作業上傳／題庫作業上傳兩個分頁。
// 作業和課程分開：選一門課、再選這門課已綁定的一位學生，填作業內容與期限，附上參考 MIDI（演奏作業）與教材。
const route = useRoute()
const router = useRouter()
const courses = ref<Course[]>([])
const students = ref<BoundStudent[]>([])
const kind = ref<Assignment['kind']>('performance')
const form = reactive({ courseId: '', studentId: '', title: '', dueDate: '', description: '' })
const midi = ref<File | null>(null)
const materials = ref<File[]>([])
const recording = ref(false)
const errors = reactive<Record<string, string>>({})
const serverError = ref('')
const saving = ref(false)
const done = ref(false)
const midiInput = ref<HTMLInputElement | null>(null)
const materialInput = ref<HTMLInputElement | null>(null)

// 只列出有學生綁定的課
const courseOptions = computed(() =>
  courses.value.filter((course) => students.value.some((student) => student.courses.some((item) => item.course_id === course.id))),
)
const studentOptions = computed(() =>
  students.value.filter((student) => student.courses.some((item) => item.course_id === form.courseId)),
)

watch(
  () => form.courseId,
  () => {
    if (!studentOptions.value.some((student) => student.id === form.studentId)) form.studentId = studentOptions.value[0]?.id ?? ''
  },
)
watch(kind, (value) => {
  if (value === 'quiz') midi.value = null
})

function onMidi(event: Event) {
  midi.value = (event.target as HTMLInputElement).files?.[0] ?? null
  delete errors.midi
}

function onMaterials(event: Event) {
  const input = event.target as HTMLInputElement
  materials.value.push(...Array.from(input.files ?? []))
  input.value = ''
}

// 「錄製音檔」：老師錄的示範也當成一份教材
function addRecording(audio: Blob, filename: string) {
  materials.value.push(new File([audio], `示範錄音-${new Date().toLocaleTimeString('zh-TW', { hour12: false })}${filename.slice(filename.lastIndexOf('.'))}`, { type: audio.type }))
  recording.value = false
}

function validate() {
  for (const key of Object.keys(errors)) delete errors[key]
  if (!form.courseId) errors.course = '請選擇課程。'
  if (!form.studentId) errors.student = '請選擇學生。'
  if (!form.title.trim()) errors.title = '請填寫作業內容。'
  if (midi.value && !/\.midi?$/i.test(midi.value.name)) errors.midi = '請選擇 .mid 或 .midi 檔。'
  if (kind.value === 'performance' && !midi.value) errors.midi = '演奏作業需要參考 MIDI，學生錄音會跟它比對。'
  return Object.keys(errors).length === 0
}

async function save() {
  serverError.value = ''
  if (!validate()) return
  saving.value = true
  try {
    await createAssignment({
      course_id: form.courseId,
      student_id: form.studentId,
      kind: kind.value,
      title: form.title.trim(),
      description: form.description.trim(),
      due_at: form.dueDate ? new Date(`${form.dueDate}T23:59:00`).toISOString() : null,
      midi: kind.value === 'performance' ? midi.value : null,
      materials: materials.value,
    })
    done.value = true
  } catch (problem) {
    serverError.value = problem instanceof Error ? problem.message : '作業沒有發布成功。'
  } finally {
    saving.value = false
  }
}

function again() {
  done.value = false
  Object.assign(form, { title: '', dueDate: '', description: '' })
  midi.value = null
  materials.value = []
  if (midiInput.value) midiInput.value.value = ''
}

onMounted(async () => {
  try {
    ;[courses.value, students.value] = await Promise.all([fetchMyCourses(), fetchMyStudents()])
  } catch (problem) {
    serverError.value = problem instanceof Error ? problem.message : '讀不到課程與學生。'
  }
  const wanted = typeof route.query.course === 'string' ? route.query.course : ''
  form.courseId = courseOptions.value.some((course) => course.id === wanted) ? wanted : (courseOptions.value[0]?.id ?? '')
})
</script>

<template>
  <PageHeader title="作業管理">
    <RouterLink to="/teacher/practice" class="btn btn--ghost">返回</RouterLink>
    <button type="submit" form="assignment-form" class="btn btn--primary" :disabled="saving">{{ saving ? '儲存中…' : '儲存' }}</button>
  </PageHeader>

  <div class="chip-group upload__tabs" role="tablist" aria-label="作業類型">
    <button type="button" role="tab" class="chip" :aria-pressed="kind === 'performance'" :aria-selected="kind === 'performance'" @click="kind = 'performance'">
      演奏作業上傳
    </button>
    <button type="button" role="tab" class="chip" :aria-pressed="kind === 'quiz'" :aria-selected="kind === 'quiz'" @click="kind = 'quiz'">
      題庫作業上傳
    </button>
  </div>

  <div v-if="courseOptions.length === 0 && courses.length" class="card empty">
    還沒有學生綁定你的課程。學生用綁定碼加入後，才能發作業給他。
  </div>

  <form v-else id="assignment-form" class="upload" novalidate @submit.prevent="save">
    <div class="field">
      <label class="field__label" for="assignment-course">選擇課程</label>
      <select id="assignment-course" v-model="form.courseId" class="select" :aria-invalid="Boolean(errors.course)">
        <option v-for="course in courseOptions" :key="course.id" :value="course.id">{{ course.title }}</option>
      </select>
      <p v-if="errors.course" class="error-text">{{ errors.course }}</p>
    </div>
    <div class="field">
      <label class="field__label" for="assignment-student">選擇學生</label>
      <select id="assignment-student" v-model="form.studentId" class="select" :aria-invalid="Boolean(errors.student)">
        <option v-for="student in studentOptions" :key="student.id" :value="student.id">{{ student.name }}</option>
      </select>
      <p v-if="errors.student" class="error-text">{{ errors.student }}</p>
    </div>
    <div class="field">
      <label class="field__label" for="assignment-title">作業內容</label>
      <input
        id="assignment-title"
        v-model="form.title"
        class="input"
        maxlength="200"
        :placeholder="kind === 'performance' ? '例如：練習給愛麗絲第 1～16 小節' : '例如：第三課樂理題目'"
        :aria-invalid="Boolean(errors.title)"
      />
      <p v-if="errors.title" class="error-text">{{ errors.title }}</p>
    </div>
    <div class="field">
      <label class="field__label" for="assignment-due">繳交期限</label>
      <input id="assignment-due" v-model="form.dueDate" class="input" type="date" />
      <span class="field__hint">不填就是「待定」。</span>
    </div>

    <div v-if="kind === 'performance'" class="field">
      <span class="field__label">參考 MIDI</span>
      <div class="file-row">
        <span class="file-row__name">{{ midi ? midi.name : '學生錄音會跟這首曲子比對音高與節奏' }}</span>
        <label class="file-row__action">
          選擇檔案
          <input ref="midiInput" type="file" accept=".mid,.midi" class="visually-hidden" @change="onMidi" />
        </label>
      </div>
      <span class="field__hint">.mid／.midi，最大 2 MB。</span>
      <p v-if="errors.midi" class="error-text">{{ errors.midi }}</p>
    </div>

    <div class="field">
      <span class="field__label">上傳教材</span>
      <ul v-if="materials.length" class="materials">
        <li v-for="(file, index) in materials" :key="`${file.name}-${index}`">
          <span>{{ file.name }}</span>
          <span class="muted">{{ fileSizeText(file.size) }}</span>
          <button type="button" class="btn btn--ghost btn--small" @click="materials.splice(index, 1)">移除</button>
        </li>
      </ul>
      <div class="file-row">
        <span class="file-row__name">樂譜、講義、示範音檔都可以，最多 10 個、每個 30 MB 以內</span>
        <label class="file-row__action">
          選擇檔案
          <input ref="materialInput" type="file" multiple class="visually-hidden" @change="onMaterials" />
        </label>
        <button type="button" class="file-row__action" @click="recording = !recording">{{ recording ? '取消錄音' : '錄製音檔' }}</button>
      </div>
      <div v-if="recording" class="card upload__recorder">
        <AudioRecorder @submit="addRecording" />
      </div>
    </div>

    <div class="field">
      <label class="field__label" for="assignment-description">備註（選填）</label>
      <textarea id="assignment-description" v-model="form.description" class="textarea" maxlength="2000" placeholder="想提醒學生的練習重點"></textarea>
    </div>

    <p v-if="serverError" class="error-text" role="alert">{{ serverError }}</p>
  </form>

  <NoticeDialog
    :open="done"
    message="作業已發布！"
    detail="學生在自己的「作業」頁就看得到，也能下載參考 MIDI 與教材。"
    confirm-text="回作業狀態"
    cancel-text="再發一份"
    @confirm="router.push('/teacher/practice')"
    @cancel="again"
  />
</template>

<style scoped>
.upload__tabs {
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 2px solid var(--home-line);
}

.upload {
  max-width: 720px;
}

.file-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
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

.materials {
  margin: 0 0 8px;
  padding: 0;
  list-style: none;
}

.materials li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  font-size: 14px;
}

.materials li span:first-child {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload__recorder {
  margin-top: 10px;
}
</style>
