<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import RecordDialog from '@/components/console/RecordDialog.vue'
import QuizQuestionCard from '@/components/console/QuizQuestionCard.vue'
import { useLeaveGuard } from '@/composables/useLeaveGuard'
import { createAssignment, fetchMyCourses, fetchMyStudents, generateQuiz } from '@/api/teacher'
import type { Assignment, BoundStudent, Course, QuizDifficulty, QuizDraftQuestion, QuizQuestionType } from '@/types/api'
import { fileSizeText } from '@/utils/format'

// 設計稿的「作業管理」：演奏作業上傳／題庫作業上傳兩個分頁。
// 演奏作業：選課程與學生、期限、參考 MIDI 與教材（教材可以當場錄示範音檔）。
// 題庫作業：上傳教材（PDF／TXT）＋出題設定，按「AI 生成題目並預覽」看 AI 出的題，滿意就「儲存題目」，再「儲存作業」發給學生。
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
const dirty = ref(false)
const midiInput = ref<HTMLInputElement | null>(null)

// ---------- 題庫作業
const COUNT_PRESETS = [10, 20, 25]
const TYPE_OPTIONS: { value: QuizQuestionType; label: string }[] = [
  { value: 'single', label: '單選題' },
  { value: 'multiple', label: '多選題' },
  { value: 'truefalse', label: '是非題' },
]
const DIFFICULTY_OPTIONS: { value: QuizDifficulty; label: string }[] = [
  { value: 'easy', label: '簡單' },
  { value: 'medium', label: '中等' },
  { value: 'hard', label: '困難' },
  { value: 'mixed', label: '混合' },
]
const quiz = reactive({
  file: null as File | null,
  count: 10 as number | 'custom',
  customCount: '' as number | '',
  types: ['single'] as QuizQuestionType[],
  difficulty: 'easy' as QuizDifficulty,
})
const preview = ref<QuizDraftQuestion[]>([])
// 老師按過「儲存題目」的題目，儲存作業時送這份
const questions = ref<QuizDraftQuestion[]>([])
const previewing = ref(false)
const previewIndex = ref(0)
const generating = ref(false)
const quizFileInput = ref<HTMLInputElement | null>(null)

const previewQuestion = computed(() => preview.value[previewIndex.value])
const questionCount = computed(() => (quiz.count === 'custom' ? Number(quiz.customCount) : quiz.count))

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
watch([() => form.title, () => form.dueDate, () => form.description, midi, materials, () => quiz.file, questions], () => (dirty.value = true), {
  deep: true,
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

function onQuizFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  input.value = ''
  if (!file) return
  if (!/\.(pdf|txt)$/i.test(file.name)) {
    errors.quizFile = '題庫檔案請選 PDF 或 TXT。'
    return
  }
  if (file.size > 20 * 1024 * 1024) {
    errors.quizFile = '題庫檔案最大 20 MB。'
    return
  }
  delete errors.quizFile
  quiz.file = file
}

function toggleType(value: QuizQuestionType) {
  quiz.types = quiz.types.includes(value) ? quiz.types.filter((item) => item !== value) : [...quiz.types, value]
}

function clearErrors() {
  for (const key of Object.keys(errors)) delete errors[key]
  serverError.value = ''
}

function validateAssign() {
  if (!form.courseId) errors.course = '請選擇課程。'
  if (!form.studentId) errors.student = '請選擇學生。'
  if (!form.title.trim()) errors.title = kind.value === 'quiz' ? '請填寫作業名稱。' : '請填寫作業標題。'
}

function validateSettings() {
  if (!quiz.file) errors.quizFile = '請選擇題庫檔案。'
  const count = questionCount.value
  if (!Number.isInteger(count) || count < 1 || count > 30) errors.count = '出題數量請填 1～30 題。'
  if (quiz.types.length === 0) errors.types = '請至少選一種題目類型。'
}

async function generate() {
  clearErrors()
  validateSettings()
  if (Object.keys(errors).length) return
  generating.value = true
  try {
    const result = await generateQuiz({ file: quiz.file!, count: questionCount.value, types: quiz.types, difficulty: quiz.difficulty })
    preview.value = result.questions
    previewIndex.value = 0
    previewing.value = true
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (problem) {
    serverError.value = problem instanceof Error ? problem.message : 'AI 出題失敗，請再試一次。'
  } finally {
    generating.value = false
  }
}

function keepQuestions() {
  questions.value = preview.value
  previewing.value = false
  delete errors.questions
}

async function save() {
  clearErrors()
  validateAssign()
  if (kind.value === 'performance') {
    if (midi.value && !/\.midi?$/i.test(midi.value.name)) errors.midi = '請選擇 .mid 或 .midi 檔。'
    if (!midi.value) errors.midi = '演奏作業需要參考 MIDI，學生錄音會跟它比對。'
  } else if (questions.value.length === 0) {
    errors.questions = '請先按「AI 生成題目並預覽」，確認題目後按「儲存題目」。'
  }
  if (Object.keys(errors).length) return
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
      materials: kind.value === 'performance' ? materials.value : [],
      questions: kind.value === 'quiz' ? questions.value : undefined,
    })
    dirty.value = false
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
  quiz.file = null
  preview.value = []
  questions.value = []
  if (midiInput.value) midiInput.value.value = ''
  setTimeout(() => (dirty.value = false))
}

// 設計稿的「變更資料未儲存，是否確認離開？」
const guard = useLeaveGuard(dirty)

onMounted(async () => {
  try {
    ;[courses.value, students.value] = await Promise.all([fetchMyCourses(), fetchMyStudents()])
  } catch (problem) {
    serverError.value = problem instanceof Error ? problem.message : '讀不到課程與學生。'
  }
  const wanted = typeof route.query.course === 'string' ? route.query.course : ''
  form.courseId = courseOptions.value.some((course) => course.id === wanted) ? wanted : (courseOptions.value[0]?.id ?? '')
  setTimeout(() => (dirty.value = false))
})
</script>

<template>
  <PageHeader :title="previewing ? 'AI 出題結果' : '作業管理'">
    <button v-if="!previewing" type="submit" form="assignment-form" class="btn btn--primary" :disabled="saving || generating">
      {{ saving ? '儲存中…' : '儲存' }}
    </button>
    <button v-else type="button" class="btn btn--primary" @click="keepQuestions">儲存</button>
  </PageHeader>

  <!-- AI 出題結果：一題一題預覽 -->
  <section v-if="previewing" class="preview">
    <div class="preview__head">
      <p class="preview__title">{{ form.title.trim() || quiz.file?.name.replace(/\.[^.]+$/, '') }}｜單元測驗</p>
      <span class="muted">共 {{ preview.length }} 題</span>
    </div>
    <QuizQuestionCard
      v-if="previewQuestion"
      mode="preview"
      :index="previewIndex"
      :total="preview.length"
      :type="previewQuestion.type"
      :difficulty="previewQuestion.difficulty"
      :topic="previewQuestion.topic"
      :question="previewQuestion.question"
      :options="previewQuestion.options"
      :answers="previewQuestion.answers"
      :explanation="previewQuestion.explanation"
      :hint="previewQuestion.hint"
      @prev="previewIndex--"
      @next="previewIndex++"
    />
    <p v-if="preview.length < questionCount" class="muted preview__short">
      教材內容只夠出 {{ preview.length }} 題（要求 {{ questionCount }} 題）。
    </p>
    <p v-if="serverError" class="error-text" role="alert">{{ serverError }}</p>
    <div class="preview__actions">
      <button type="button" class="btn btn--ghost btn--block" :disabled="generating" @click="generate">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7" />
        </svg>
        {{ generating ? 'AI 重新出題中…' : '重新生成題目' }}
      </button>
      <button type="button" class="btn btn--primary btn--block" :disabled="generating" @click="keepQuestions">儲存題目</button>
      <button type="button" class="btn btn--ghost btn--small preview__back" :disabled="generating" @click="previewing = false">回到設定</button>
    </div>
  </section>

  <template v-else>
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
      <!-- 演奏作業 -->
      <template v-if="kind === 'performance'">
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
          <label class="field__label" for="assignment-title">作業標題</label>
          <input
            id="assignment-title"
            v-model="form.title"
            class="input"
            maxlength="200"
            placeholder="例如：練習給愛麗絲第 1～16 小節"
            :aria-invalid="Boolean(errors.title)"
          />
          <p v-if="errors.title" class="error-text">{{ errors.title }}</p>
        </div>
        <div class="field">
          <label class="field__label" for="assignment-due">繳交期限</label>
          <input id="assignment-due" v-model="form.dueDate" class="input" type="date" />
          <span class="field__hint">不填就是「待定」。</span>
        </div>
        <div class="field">
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
          <span class="field__label">上傳作業</span>
          <ul v-if="materials.length" class="materials">
            <li v-for="(file, index) in materials" :key="`${file.name}-${index}`">
              <span>{{ file.name }}</span>
              <span class="muted">{{ fileSizeText(file.size) }}</span>
              <button type="button" class="btn btn--ghost btn--small" @click="materials.splice(index, 1)">移除</button>
            </li>
          </ul>
          <div class="file-row">
            <span class="file-row__name">樂譜、講義、示範音檔都可以，最多 10 個、每個 30 MB 以內</span>
          </div>
          <div class="file-row__links">
            <label class="file-row__action">
              選擇檔案
              <input type="file" multiple class="visually-hidden" @change="onMaterials" />
            </label>
            <button type="button" class="file-row__action" @click="recording = true">錄製音檔</button>
          </div>
        </div>
        <div class="field">
          <label class="field__label" for="assignment-description">備註（選填）</label>
          <textarea id="assignment-description" v-model="form.description" class="textarea" maxlength="2000" placeholder="想提醒學生的練習重點"></textarea>
        </div>
      </template>

      <!-- 題庫作業 -->
      <template v-else>
        <h2 class="upload__section">題庫作業上傳</h2>
        <div class="field">
          <label class="field__label" for="quiz-title">作業名稱</label>
          <input
            id="quiz-title"
            v-model="form.title"
            class="input"
            maxlength="200"
            placeholder="例如：基礎樂理"
            :aria-invalid="Boolean(errors.title)"
          />
          <p v-if="errors.title" class="error-text">{{ errors.title }}</p>
        </div>
        <div class="field">
          <span class="field__label">題庫檔案</span>
          <label class="dropzone" :class="{ 'dropzone--filled': quiz.file }">
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M12 17v-6M9.5 13.5 12 11l2.5 2.5" />
            </svg>
            <strong>{{ quiz.file ? quiz.file.name : '選擇題庫檔案' }}</strong>
            <span class="muted">{{ quiz.file ? `${fileSizeText(quiz.file.size)}・點這裡換一份` : '支援 PDF、TXT 格式，最大 20 MB' }}</span>
            <input ref="quizFileInput" type="file" accept=".pdf,.txt,application/pdf,text/plain" class="visually-hidden" @change="onQuizFile" />
          </label>
          <p v-if="errors.quizFile" class="error-text">{{ errors.quizFile }}</p>
        </div>

        <h2 class="upload__section">出題設定</h2>
        <fieldset class="panel">
          <legend class="panel__legend">出題數量</legend>
          <label v-for="preset in COUNT_PRESETS" :key="preset" class="option">
            <input v-model="quiz.count" type="radio" name="quiz-count" :value="preset" /> {{ preset }} 題
          </label>
          <label class="option option--custom">
            <input v-model="quiz.count" type="radio" name="quiz-count" value="custom" /> 自訂題數
            <input
              v-model.number="quiz.customCount"
              class="input"
              type="number"
              min="1"
              max="30"
              placeholder="1～30"
              aria-label="自訂題數"
              @focus="quiz.count = 'custom'"
            />
          </label>
          <p v-if="errors.count" class="error-text">{{ errors.count }}</p>
        </fieldset>
        <fieldset class="panel">
          <legend class="panel__legend">題目類型（可複選）</legend>
          <label v-for="option in TYPE_OPTIONS" :key="option.value" class="option">
            <input type="checkbox" :checked="quiz.types.includes(option.value)" @change="toggleType(option.value)" /> {{ option.label }}
          </label>
          <p v-if="errors.types" class="error-text">{{ errors.types }}</p>
        </fieldset>
        <fieldset class="panel">
          <legend class="panel__legend">難易度</legend>
          <label v-for="option in DIFFICULTY_OPTIONS" :key="option.value" class="option">
            <input v-model="quiz.difficulty" type="radio" name="quiz-difficulty" :value="option.value" /> {{ option.label }}
          </label>
        </fieldset>

        <h2 class="upload__section">指派與繳交設定</h2>
        <fieldset class="panel">
          <div class="field">
            <label class="field__label" for="quiz-course">選擇課程</label>
            <select id="quiz-course" v-model="form.courseId" class="select" :aria-invalid="Boolean(errors.course)">
              <option v-for="course in courseOptions" :key="course.id" :value="course.id">{{ course.title }}</option>
            </select>
            <p v-if="errors.course" class="error-text">{{ errors.course }}</p>
          </div>
          <div class="field">
            <label class="field__label" for="quiz-student">選擇學生</label>
            <select id="quiz-student" v-model="form.studentId" class="select" :aria-invalid="Boolean(errors.student)">
              <option v-for="student in studentOptions" :key="student.id" :value="student.id">{{ student.name }}</option>
            </select>
            <p v-if="errors.student" class="error-text">{{ errors.student }}</p>
          </div>
          <div class="field">
            <label class="field__label" for="quiz-due">繳交期限</label>
            <input id="quiz-due" v-model="form.dueDate" class="input" type="date" />
          </div>
        </fieldset>

        <div v-if="questions.length" class="card ready" role="status">
          <span>已儲存 {{ questions.length }} 題，按「儲存作業」就會發給學生。</span>
          <button type="button" class="btn btn--ghost btn--small" @click="preview = questions; previewIndex = 0; previewing = true">再看一次</button>
        </div>
        <p v-if="errors.questions" class="error-text">{{ errors.questions }}</p>
        <p v-if="generating" class="muted" role="status">AI 正在讀教材出題，大約需要半分鐘到一分鐘…</p>

        <div class="upload__buttons">
          <button type="button" class="btn btn--primary btn--block" :disabled="generating || saving" @click="generate">
            {{ generating ? 'AI 出題中…' : 'AI 生成題目並預覽' }}
          </button>
          <button type="submit" class="btn btn--primary btn--block" :disabled="generating || saving">
            {{ saving ? '儲存中…' : '儲存作業' }}
          </button>
        </div>
      </template>

      <p v-if="serverError" class="error-text" role="alert">{{ serverError }}</p>
    </form>
  </template>

  <RecordDialog :open="recording" hint="錄好的示範會當成一份教材給學生" @close="recording = false" @done="addRecording" />

  <NoticeDialog
    :open="done"
    message="更新成功！"
    detail="作業已發給學生，學生在自己的「作業」頁就看得到。"
    confirm-text="確認"
    cancel-text="再發一份"
    @confirm="router.push('/teacher/practice')"
    @cancel="again"
  />
  <NoticeDialog
    :open="guard.asking.value"
    message="變更資料未儲存，是否確認離開？"
    confirm-text="確認"
    cancel-text="取消"
    @confirm="guard.leave"
    @cancel="guard.stay"
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

.upload__section {
  margin: 26px 0 12px;
  padding-top: 18px;
  border-top: 1px solid var(--home-line);
  font-size: 17px;
}

.upload__section:first-child {
  margin-top: 0;
  padding-top: 0;
  border-top: 0;
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

.dropzone {
  display: grid;
  justify-items: center;
  gap: 4px;
  padding: 22px 16px;
  border: 1px solid var(--home-line);
  border-radius: 22px;
  background: #fff;
  color: var(--home-ink);
  text-align: center;
  cursor: pointer;
}

.dropzone:hover,
.dropzone:focus-within {
  border-color: var(--home-accent);
}

.dropzone strong {
  font-size: 15px;
  word-break: break-all;
}

.dropzone .muted {
  font-size: 13px;
}

.dropzone--filled {
  background: var(--home-cream);
}

.panel {
  margin: 0 0 14px;
  padding: 12px 18px 14px;
  border: 1px solid var(--home-line);
  border-radius: 18px;
  background: #f7f4f0;
}

.panel__legend {
  float: left;
  width: 100%;
  margin-bottom: 6px;
  color: var(--home-muted);
  font-size: 13px;
}

.panel .field {
  clear: both;
}

.option {
  display: flex;
  align-items: center;
  gap: 10px;
  clear: both;
  padding: 6px 0;
  font-size: 14px;
  cursor: pointer;
}

.option input[type='radio'],
.option input[type='checkbox'] {
  width: 16px;
  height: 16px;
  accent-color: var(--home-accent);
}

.option--custom .input {
  width: 110px;
  min-height: 34px;
}

.ready {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 6px;
  font-size: 14px;
}

.upload__buttons {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.preview {
  max-width: 720px;
}

.preview__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin: -8px 0 14px;
}

.preview__title {
  margin: 0;
  color: var(--home-muted);
}

.preview__short {
  margin: 10px 0 0;
  font-size: 13px;
}

.preview__actions {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.preview__back {
  justify-self: center;
}
</style>
