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
      <span aria-hidden="true">✦</span> AI 找課
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
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: 1px solid var(--home-line);
  border-radius: var(--radius-pill);
  background: var(--home-paper);
  color: var(--home-ink);
  font-size: 15px;
  cursor: pointer;
  box-shadow: 0 10px 28px rgba(80, 58, 40, 0.16);
  transition: background 0.2s ease;
}

.ai-assist__button span {
  color: var(--home-accent);
}

.ai-assist__button:hover {
  background: var(--home-cream);
}

.ai-assist__panel {
  width: min(300px, calc(100vw - 48px));
  padding: 16px;
  background: var(--home-paper);
  border: 1px solid var(--home-line);
  border-radius: 20px;
  box-shadow: var(--shadow-soft);
  color: var(--home-muted);
  font-size: 14px;
  line-height: 1.7;
}

.ai-assist__panel p {
  margin: 0;
}

.ai-assist__title {
  margin-bottom: 8px !important;
  color: var(--home-ink);
  font-weight: 500;
}

@media (max-width: 760px) {
  .ai-assist {
    right: 16px;
    bottom: 16px;
  }

  .ai-assist__button {
    padding: 10px 16px;
    font-size: 14px;
  }
}
</style>
