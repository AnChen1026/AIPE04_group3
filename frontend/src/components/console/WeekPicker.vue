<script setup lang="ts">
import { computed } from 'vue'
import { addDays, startOfWeek } from '@/utils/format'

// 設計稿的「‹ 2026年10月 › 」：左右換週，中間顯示這週的年月
const weekStart = defineModel<Date>({ required: true })

const label = computed(() => {
  const end = addDays(weekStart.value, 6)
  const start = weekStart.value
  const head = `${start.getFullYear()}年${start.getMonth() + 1}月${start.getDate()}日`
  const tail = start.getMonth() === end.getMonth() ? `${end.getDate()}日` : `${end.getMonth() + 1}月${end.getDate()}日`
  return `${head}－${tail}`
})

function move(weeks: number) {
  weekStart.value = addDays(weekStart.value, weeks * 7)
}
</script>

<template>
  <div class="picker">
    <button type="button" class="picker__arrow" aria-label="上一週" @click="move(-1)">‹</button>
    <span class="picker__label">{{ label }}</span>
    <button type="button" class="picker__arrow" aria-label="下一週" @click="move(1)">›</button>
    <button type="button" class="btn btn--ghost btn--small" @click="weekStart = startOfWeek(new Date())">本週</button>
  </div>
</template>

<style scoped>
.picker {
  display: flex;
  align-items: center;
  gap: 8px;
}

.picker__label {
  min-width: 190px;
  padding: 6px 14px;
  border: 1px solid var(--home-line);
  border-radius: var(--radius-pill);
  background: var(--home-paper);
  font-size: 14px;
  text-align: center;
}

.picker__arrow {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--home-ink);
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.picker__arrow:hover {
  background: var(--home-cream);
}
</style>
