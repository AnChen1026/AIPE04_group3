<script setup lang="ts">
import { inject } from 'vue'
import { SHELL_TOP_ACTIONS } from './shell'

// 每頁的標題與說明。老師後台、學生專區照設計稿把按鈕、搜尋框放到外框上方的標題列；管理員後台維持放在標題右邊
defineProps<{ title: string; description?: string }>()

const topActions = inject(SHELL_TOP_ACTIONS, false)
</script>

<template>
  <div class="page-header">
    <div>
      <h1>{{ title }}</h1>
      <p v-if="description">{{ description }}</p>
    </div>
    <Teleport v-if="$slots.default" defer to="#shell-actions" :disabled="!topActions">
      <div class="page-header__actions"><slot /></div>
    </Teleport>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 22px;
}

.page-header h1 {
  margin: 0;
  color: var(--home-ink);
  font-size: clamp(24px, 2.4vw, 30px);
  font-weight: 500;
}

.page-header p {
  margin: 6px 0 0;
  color: var(--home-muted);
  font-size: 14px;
}

/* 搜尋框和按鈕固定同一排；搜尋框寬度是百分比，允許換行時按鈕會被擠到下一排 */
.page-header__actions {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 10px;
}

.page-header__actions :slotted(.btn) {
  flex-shrink: 0;
  white-space: nowrap;
}
</style>
