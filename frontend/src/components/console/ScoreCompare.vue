<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { OpenSheetMusicDisplay } from 'opensheetmusicdisplay'

// 上下對照樂譜：後端產生的 MusicXML 裡有兩行（答案、你的演奏），每個小節上下對齊。
// 顏色是後端標的，這裡只負責畫出來。樂譜套件很大，打開時才載入。
const props = defineProps<{ url: string }>()

const container = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const error = ref('')
let display: OpenSheetMusicDisplay | null = null

onMounted(async () => {
  try {
    const response = await fetch(props.url, { credentials: 'include' })
    if (!response.ok) throw new Error('讀不到這次的對照樂譜。')
    const xml = await response.text()
    const { OpenSheetMusicDisplay } = await import('opensheetmusicdisplay')
    display = new OpenSheetMusicDisplay(container.value!, {
      autoResize: true,
      drawTitle: false,
      drawComposer: false,
      drawPartNames: true,
      drawMeasureNumbers: true,
      backend: 'svg',
    })
    await display.load(xml)
    display.render()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '對照樂譜顯示失敗。'
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  display?.clear()
  display = null
})
</script>

<template>
  <div class="compare">
    <ul class="compare__legend" aria-label="顏色說明">
      <li><span class="compare__swatch compare__swatch--wrong"></span>彈錯音高（答案行：沒彈對的音）</li>
      <li><span class="compare__swatch compare__swatch--extra"></span>多彈的音（不扣分）</li>
      <li><span class="compare__swatch compare__swatch--rhythm"></span>音對了，時間不對</li>
    </ul>
    <p v-if="loading" class="muted">樂譜載入中…</p>
    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    <div ref="container" class="compare__sheet"></div>
  </div>
</template>

<style scoped>
.compare {
  margin-top: 10px;
  padding: 12px;
  border: 1px solid var(--home-line);
  border-radius: 16px;
  background: #fff;
}

.compare__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  margin: 0 0 6px;
  padding: 0;
  font-size: 13px;
  list-style: none;
}

.compare__legend li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* 和後端 score_sheet.py 的顏色一致 */
.compare__swatch {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.compare__swatch--wrong {
  background: #d0342c;
}

.compare__swatch--extra {
  background: #e08a00;
}

.compare__swatch--rhythm {
  background: #2f6fd0;
}

.compare__sheet {
  overflow-x: auto;
}
</style>
