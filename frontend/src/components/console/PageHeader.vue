<script setup lang="ts">
// 每頁上方的標題列：左邊標題與說明，右邊放按鈕
defineProps<{ title: string; description?: string }>()
</script>

<template>
  <div class="page-header">
    <div>
      <h1>{{ title }}</h1>
      <p v-if="description">{{ description }}</p>
    </div>
    <div v-if="$slots.default" class="page-header__actions"><slot /></div>
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

.page-header__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
</style>
