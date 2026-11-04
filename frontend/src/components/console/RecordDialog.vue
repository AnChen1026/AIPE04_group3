<script setup lang="ts">
import AudioRecorder from './AudioRecorder.vue'

// 設計稿的「錄製音檔」視窗：錄音或選一個音檔，確認後交給呼叫的頁面（老師當示範教材、學生當作業繳交）。
// 不帶節拍器：設計稿的錄音視窗沒有節拍器。
defineProps<{ open: boolean; hint?: string }>()
const emit = defineEmits<{ close: []; done: [audio: Blob, filename: string] }>()
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="record" @click.self="emit('close')" @keydown.esc="emit('close')">
      <div class="record__box" role="dialog" aria-modal="true" aria-labelledby="record-title">
        <header class="record__head">
          <h2 id="record-title">錄製音檔</h2>
          <button type="button" class="record__close" aria-label="關閉" @click="emit('close')">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M6 6l12 12M18 6 6 18" />
            </svg>
          </button>
        </header>
        <div class="record__body">
          <span class="record__icon" aria-hidden="true">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <path d="M4 10v4M8 7v10M12 4v16M16 7v10M20 10v4" />
            </svg>
          </span>
          <p class="record__title">準備錄製</p>
          <p v-if="hint" class="record__hint">{{ hint }}</p>
          <AudioRecorder @submit="(audio, filename) => emit('done', audio, filename)" />
        </div>
        <footer class="record__foot">
          <button type="button" class="btn btn--ghost btn--block" @click="emit('close')">取消</button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.record {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(62, 52, 44, 0.32);
}

.record__box {
  width: min(460px, 100%);
  max-height: calc(100vh - 32px);
  overflow-y: auto;
  padding: 22px 26px;
  border-radius: 24px;
  background: var(--home-paper);
  box-shadow: 0 20px 48px rgba(62, 52, 44, 0.2);
}

.record__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--home-line);
}

.record__head h2 {
  margin: 0;
  color: var(--home-accent-dark);
  font-size: 22px;
}

.record__close {
  padding: 4px;
  border: 0;
  background: none;
  color: var(--home-ink);
  cursor: pointer;
}

.record__body {
  padding: 18px 0;
  text-align: center;
}

.record__icon {
  display: inline-grid;
  width: 72px;
  height: 72px;
  place-items: center;
  border-radius: 50%;
  background: var(--home-cream);
  color: var(--home-accent);
}

.record__title {
  margin: 10px 0 0;
  font-size: 17px;
}

.record__hint {
  margin: 2px 0 12px;
  color: var(--home-muted);
  font-size: 13px;
}

.record__body :deep(.recorder) {
  flex-direction: column;
  align-items: stretch;
}

.record__foot {
  padding-top: 14px;
  border-top: 1px solid var(--home-line);
}
</style>
