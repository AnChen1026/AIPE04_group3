<script setup lang="ts">
import { ref } from 'vue'

// AI聊天視窗（首頁推薦）尚未串接，先提供開關與說明
const open = ref(false)
</script>

<template>
  <div class="ai-assist">
    <div v-if="open" class="ai-assist__panel" role="dialog" aria-label="AI 找課助理">
      <p class="ai-assist__title">AI 找課助理</p>
      <p>描述你想學的鋼琴內容，系統會從已發布課程中推薦。此功能開發中。</p>
    </div>
    <button type="button" class="ai-assist__button" :aria-expanded="open" @click="open = !open">
      AI協助
    </button>
  </div>
</template>

<style scoped>
.ai-assist {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 20;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.ai-assist__button {
  width: 76px;
  height: 76px;
  border: 0;
  border-radius: 50%;
  background: var(--color-ai-button);
  font-size: 18px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgb(0 0 0 / 12%);
}

.ai-assist__button:hover {
  filter: brightness(0.96);
}

.ai-assist__panel {
  width: min(300px, calc(100vw - 48px));
  padding: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  box-shadow: 0 8px 24px rgb(0 0 0 / 12%);
  font-size: 15px;
}

.ai-assist__panel p {
  margin: 0;
}

.ai-assist__title {
  margin-bottom: 8px !important;
  font-weight: 700;
}

@media (max-width: 760px) {
  .ai-assist {
    right: 16px;
    bottom: 16px;
  }

  .ai-assist__button {
    width: 60px;
    height: 60px;
    font-size: 15px;
  }
}
</style>
