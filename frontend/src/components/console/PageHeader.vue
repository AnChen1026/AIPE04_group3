<script setup lang="ts">
import { inject } from 'vue'
import { SHELL_TOP_ACTIONS } from './shell'

// 每頁的標題與說明。老師後台、學生專區照設計稿把按鈕、搜尋框放到外框上方的標題列；管理員後台維持放在標題右邊。
// title-actions 是一定留在頁面標題同一行右邊的按鈕（例如課表的「編輯時段」），不會被搬到外框上方
defineProps<{ title: string; description?: string }>()

const topActions = inject(SHELL_TOP_ACTIONS, false)
</script>

<template>
  <div class="page-header">
    <div class="page-header__main">
      <div class="page-header__title">
        <h1>{{ title }}</h1>
        <div v-if="$slots['title-actions']" class="page-header__title-actions"><slot name="title-actions" /></div>
      </div>
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

.page-header__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
</style>
