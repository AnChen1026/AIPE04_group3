<script setup lang="ts">
// 標題下面的一列：左邊放篩選（全部／已發布…、圖例），右邊放搜尋框和按鈕（新增、儲存、編輯時段…）。
// 老師後台照 UIUX 回饋把這些按鈕從外框上方的標題列移到這一列；左邊沒有東西時按鈕一樣靠右
defineProps<{ divider?: boolean }>()
</script>

<template>
  <div class="page-toolbar" :class="{ 'page-toolbar--divider': divider }">
    <div class="page-toolbar__start"><slot /></div>
    <div v-if="$slots.actions" class="page-toolbar__actions"><slot name="actions" /></div>
  </div>
</template>

<style scoped>
.page-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px 16px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

/* 作業、課程頁的篩選列下面有一條分隔線 */
.page-toolbar--divider {
  padding-bottom: 14px;
  border-bottom: 2px solid var(--home-line);
}

.page-toolbar__start {
  /* 左邊（篩選、圖例）先縮、自己換行，右邊的按鈕才留得在同一列；窄到 240px 以下才整列換行 */
  flex: 1 1 240px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
}

.page-toolbar__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.page-toolbar__actions :slotted(.btn) {
  flex-shrink: 0;
  white-space: nowrap;
}

/* 搜尋框給固定寬度，才不會被按鈕擠到只剩一點點 */
.page-toolbar__actions :slotted(.search-input) {
  width: 220px;
  max-width: 100%;
}

@media (max-width: 640px) {
  .page-toolbar__actions {
    flex-wrap: wrap;
    margin-left: 0;
  }
}
</style>
