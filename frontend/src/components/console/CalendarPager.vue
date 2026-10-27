<script setup lang="ts">
import { computed } from 'vue'
import { addDays, startOfWeek } from '@/utils/format'

export type CalendarMode = 'day' | 'week' | 'month'

// 課表右上方：切換「日／週／月」，左右箭頭換上一段、下一段，「今天」跳回現在
const anchor = defineModel<Date>({ required: true })
const mode = defineModel<CalendarMode>('mode', { required: true })

const MODES: { value: CalendarMode; label: string }[] = [
  { value: 'day', label: '日' },
  { value: 'week', label: '週' },
  { value: 'month', label: '月' },
]
const STEP_LABELS: Record<CalendarMode, string> = { day: '天', week: '週', month: '個月' }

const label = computed(() => {
  const date = anchor.value
  if (mode.value === 'month') return `${date.getFullYear()}年${date.getMonth() + 1}月`
  if (mode.value === 'day') {
    const weekday = '日一二三四五六'[date.getDay()]
    return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日（${weekday}）`
  }
  const start = startOfWeek(date)
  const end = addDays(start, 6)
  const head = `${start.getFullYear()}年${start.getMonth() + 1}月${start.getDate()}日`
  const tail = start.getMonth() === end.getMonth() ? `${end.getDate()}日` : `${end.getMonth() + 1}月${end.getDate()}日`
  return `${head}－${tail}`
})

function move(direction: number) {
  const date = anchor.value
  if (mode.value === 'month') anchor.value = new Date(date.getFullYear(), date.getMonth() + direction, 1)
  else anchor.value = addDays(date, direction * (mode.value === 'week' ? 7 : 1))
}
</script>

<template>
  <div class="pager">
    <div class="pager__modes" role="group" aria-label="顯示方式">
      <button
        v-for="item in MODES"
        :key="item.value"
        type="button"
        class="pager__mode"
        :aria-pressed="mode === item.value"
        @click="mode = item.value"
      >
        {{ item.label }}
      </button>
    </div>
    <button type="button" class="pager__arrow" :aria-label="`上一${STEP_LABELS[mode]}`" @click="move(-1)">‹</button>
    <span class="pager__label">{{ label }}</span>
    <button type="button" class="pager__arrow" :aria-label="`下一${STEP_LABELS[mode]}`" @click="move(1)">›</button>
    <button type="button" class="btn btn--ghost btn--small" @click="anchor = new Date()">今天</button>
  </div>
</template>

<style scoped>
.pager {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pager__modes {
  display: flex;
  margin-right: 6px;
  padding: 3px;
  border: 1px solid var(--home-line);
  border-radius: var(--radius-pill);
  background: var(--home-paper);
}

.pager__mode {
  min-width: 36px;
  padding: 4px 10px;
  border: 0;
  border-radius: var(--radius-pill);
  background: none;
  color: var(--home-muted);
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

.pager__mode[aria-pressed='true'] {
  background: var(--home-accent);
  color: var(--home-paper);
}

.pager__label {
  min-width: 190px;
  padding: 6px 14px;
  border: 1px solid var(--home-line);
  border-radius: var(--radius-pill);
  background: var(--home-paper);
  font-size: 14px;
  text-align: center;
}

.pager__arrow {
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

.pager__arrow:hover {
  background: var(--home-cream);
}
</style>
