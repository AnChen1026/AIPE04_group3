<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { useMetronome } from '@/composables/useMetronome'

// 網頁錄音：按下開始才會要求麥克風權限，停止後可以先回聽，確認後才送出。
// 沒有麥克風時，改選一個錄好的音檔。
// 給了 defaultBpm 就顯示節拍器：開著錄音時，送出會帶節拍器速度，節奏照它評分；上傳音檔時不帶。
const emit = defineEmits<{ submit: [audio: Blob, filename: string, metronomeBpm: number | null] }>()
const props = defineProps<{ busy?: boolean; defaultBpm?: number | null; beatsPerBar?: number }>()

const state = ref<'idle' | 'recording' | 'ready'>('idle')
const error = ref('')
const seconds = ref(0)
const previewUrl = ref('')
const metronome = useMetronome()
const metronomeOn = ref(false)
const bpm = ref(Math.round(props.defaultBpm ?? 120))
let recorder: MediaRecorder | null = null
let stream: MediaStream | null = null
let chunks: Blob[] = []
let take: { blob: Blob; filename: string; metronomeBpm: number | null } | null = null
let tick = 0

watch(
  () => props.defaultBpm,
  (value) => {
    if (value && !metronomeOn.value) bpm.value = Math.round(value)
  },
)

function clampBpm() {
  bpm.value = Math.min(240, Math.max(30, Math.round(Number(bpm.value) || 120)))
}

// 只想跟著節拍器練、還沒要錄音時，可以先打開聽
async function toggleMetronome() {
  clampBpm()
  if (metronome.running.value) metronome.stop()
  else await metronome.start(bpm.value, props.beatsPerBar)
  metronomeOn.value = metronome.running.value
}

watch(bpm, () => {
  if (metronome.running.value && state.value !== 'recording' && bpm.value >= 30 && bpm.value <= 240) {
    metronome.start(bpm.value, props.beatsPerBar)
  }
})

const supported = typeof window !== 'undefined' && 'MediaRecorder' in window && !!navigator.mediaDevices?.getUserMedia

function setTake(blob: Blob, filename: string, metronomeBpm: number | null) {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  take = { blob, filename, metronomeBpm }
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
  // 錄音期間節拍器速度固定，送出時帶這個速度
  const recordedBpm = metronome.running.value ? bpm.value : null
  recorder = new MediaRecorder(stream)
  recorder.ondataavailable = (event) => {
    if (event.data.size > 0) chunks.push(event.data)
  }
  recorder.onstop = () => {
    const type = recorder?.mimeType || 'audio/webm'
    const extension = type.includes('mp4') ? 'm4a' : type.includes('ogg') ? 'ogg' : 'webm'
    setTake(new Blob(chunks, { type }), `practice.${extension}`, recordedBpm)
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
  metronome.stop()
  metronomeOn.value = false
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
  setTake(file, file.name, null)
  input.value = ''
}

function discard() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  take = null
  state.value = 'idle'
}

function submit() {
  if (take) emit('submit', take.blob, take.filename, take.metronomeBpm)
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
  <div v-if="defaultBpm !== undefined && state !== 'ready'" class="metronome">
    <button
      type="button"
      class="metronome__toggle"
      :aria-pressed="metronome.running.value"
      :disabled="state === 'recording'"
      @click="toggleMetronome"
    >
      <span class="metronome__light" :class="{ 'metronome__light--on': metronome.flash.value, 'metronome__light--accent': metronome.flash.value && metronome.beat.value === 0 }" aria-hidden="true"></span>
      {{ metronome.running.value ? '關閉節拍器' : '開啟節拍器' }}
    </button>
    <label class="metronome__bpm">
      <span>速度</span>
      <input v-model.number="bpm" type="number" min="30" max="240" class="input" :disabled="state === 'recording'" @change="clampBpm" />
      <span>BPM</span>
    </label>
    <p v-if="metronome.running.value" class="metronome__hint">
      請戴耳機，節拍器的聲音才不會被錄進去。開著節拍器錄音，節奏會照 {{ bpm }} BPM 評分。
    </p>
    <p v-else class="metronome__hint muted">不開也可以，節奏會照你自己彈的速度按比例評分。</p>
  </div>

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
      <span v-if="metronome.running.value" class="muted">節拍器 {{ bpm }} BPM</span>
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
.metronome {
  display: flex;
  align-items: center;
  gap: 8px 14px;
  flex-wrap: wrap;
  margin-bottom: 14px;
  padding: 12px 16px;
  border-radius: 16px;
  background: var(--home-cream);
}

.metronome__toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 36px;
  padding: 0 16px;
  border: 1px solid var(--home-wood);
  border-radius: var(--radius-pill);
  background: var(--home-paper);
  color: var(--home-ink);
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

.metronome__toggle[aria-pressed='true'] {
  border-color: var(--home-accent);
}

.metronome__light {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--home-line);
}

.metronome__light--on {
  background: var(--home-wood);
}

.metronome__light--accent {
  background: var(--home-accent);
}

.metronome__bpm {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.metronome__bpm .input {
  width: 76px;
  min-height: 34px;
  text-align: center;
}

.metronome__hint {
  flex-basis: 100%;
  margin: 0;
  font-size: 13px;
}

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
