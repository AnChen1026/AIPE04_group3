<script setup lang="ts">
import { inject } from 'vue'
import { SHELL_TOP_ACTIONS } from './shell'

// 每頁的標題與說明。學生專區照設計稿把按鈕、搜尋框放到外框上方的標題列；
// 老師後台（UIUX 回饋）和管理員後台放在頁面標題同一列的最右邊。
// title-actions 是一定留在頁面標題同一行右邊的按鈕，不會被搬到外框上方
defineProps<{ title: string; description?: string }>()

const topActions = inject(SHELL_TOP_ACTIONS, false)
</script>

<template>
  <div class="page-header">
    <div class="page-header__main">
      <div class="page-header__title">
        <h1>{{ title }}</h1>
        <div v-if="$slots['title-actions'] || (!topActions && $slots.default)" class="page-header__title-actions">
          <slot name="title-actions" />
          <slot v-if="!topActions" />
        </div>
      </div>
      <p v-if="description">{{ description }}</p>
    </div>
    <Teleport v-if="$slots.default && topActions" defer to="#shell-actions">
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

.page-header__main {
  flex: 1 1 320px;
  min-width: 0;
}

.page-header__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.page-header__title-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-header__title-actions :slotted(.btn) {
  flex-shrink: 0;
  white-space: nowrap;
}

/* 搜尋框給固定寬度，放在標題右邊時才不會被擠窄 */
.page-header__title-actions :slotted(.search-input) {
  width: 220px;
  max-width: 100%;
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
