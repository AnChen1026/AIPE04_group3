<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'

// 網頁錄音：按下開始才會要求麥克風權限，停止後可以先回聽，確認後才送出。
// 沒有麥克風時，改選一個錄好的音檔。
const emit = defineEmits<{ submit: [audio: Blob, filename: string] }>()
defineProps<{ busy?: boolean }>()

const state = ref<'idle' | 'recording' | 'ready'>('idle')
const error = ref('')
const seconds = ref(0)
const previewUrl = ref('')
let recorder: MediaRecorder | null = null
let stream: MediaStream | null = null
let chunks: Blob[] = []
let take: { blob: Blob; filename: string } | null = null
let tick = 0

const supported = typeof window !== 'undefined' && 'MediaRecorder' in window && !!navigator.mediaDevices?.getUserMedia

function setTake(blob: Blob, filename: string) {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  take = { blob, filename }
  previewUrl.value = URL.createObjectURL(blob)
  state.value = 'ready'
}

async function start() {
  error.value = ''
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  } catch {
    error.value = '沒有拿到麥克風權限。可以在瀏覽器網址列旁開啟，或改上傳錄好的音檔。'
    return
  }
  chunks = []
  recorder = new MediaRecorder(stream)
  recorder.ondataavailable = (event) => {
    if (event.data.size > 0) chunks.push(event.data)
  }
  recorder.onstop = () => {
    const type = recorder?.mimeType || 'audio/webm'
    const extension = type.includes('mp4') ? 'm4a' : type.includes('ogg') ? 'ogg' : 'webm'
    setTake(new Blob(chunks, { type }), `practice.${extension}`)
    stopStream()
  }
  recorder.start()
  seconds.value = 0
  tick = window.setInterval(() => (seconds.value += 1), 1000)
  state.value = 'recording'
}

function stop() {
  window.clearInterval(tick)
  recorder?.stop()
}

function stopStream() {
  stream?.getTracks().forEach((track) => track.stop())
  stream = null
}

function onFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 20 * 1024 * 1024) {
    error.value = '音檔最大 20 MB。'
    input.value = ''
    return
  }
  error.value = ''
  setTake(file, file.name)
  input.value = ''
}

function discard() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  take = null
  state.value = 'idle'
}

function submit() {
  if (take) emit('submit', take.blob, take.filename)
}

function clock(value: number) {
  return `${String(Math.floor(value / 60)).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}`
}

defineExpose({ discard })

onBeforeUnmount(() => {
  window.clearInterval(tick)
  if (recorder?.state === 'recording') recorder.stop()
  stopStream()
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})
</script>

<template>
  <div class="recorder">
    <template v-if="state === 'idle'">
      <button v-if="supported" type="button" class="recorder__main" @click="start">
        <span class="recorder__dot" aria-hidden="true"></span>開始錄音
      </button>
      <label class="btn btn--ghost recorder__file">
        上傳錄好的音檔
        <input type="file" accept="audio/*,.wav,.mp3,.m4a,.ogg,.webm" class="visually-hidden" @change="onFile" />
      </label>
    </template>

    <template v-else-if="state === 'recording'">
      <button type="button" class="recorder__main recorder__main--stop" @click="stop">
        <span class="recorder__square" aria-hidden="true"></span>停止
      </button>
      <span class="recorder__clock" aria-live="polite">錄音中 {{ clock(seconds) }}</span>
    </template>

    <template v-else>
      <audio :src="previewUrl" controls class="recorder__preview"></audio>
      <div class="recorder__actions">
        <button type="button" class="btn btn--ghost" :disabled="busy" @click="discard">重錄</button>
        <button type="button" class="btn btn--primary" :disabled="busy" @click="submit">{{ busy ? '送出中…' : '確認送出' }}</button>
      </div>
    </template>

    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
  </div>
</template>

<style scoped>
.recorder {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.recorder__main {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 0 24px;
  border: 0;
  border-radius: var(--radius-pill);
  background: var(--home-accent);
  color: var(--home-paper);
  font: inherit;
  font-size: 16px;
  cursor: pointer;
}

.recorder__main:hover {
  background: var(--home-accent-dark);
}

.recorder__main--stop {
  background: #9a4a35;
}

.recorder__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #f3c9bc;
}

.recorder__square {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  background: var(--home-paper);
}

.recorder__clock {
  color: #9a4a35;
  font-variant-numeric: tabular-nums;
}

.recorder__file {
  cursor: pointer;
}

.recorder__preview {
  width: min(360px, 100%);
}

.recorder__actions {
  display: flex;
  gap: 10px;
}

.error-text {
  flex-basis: 100%;
}
</style>
