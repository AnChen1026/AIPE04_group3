<script setup lang="ts">
import { computed } from 'vue'
import { addDays, formatTime, sameDay, startOfWeek } from '@/utils/format'
import { lessonColor, startOfMonth, type TimetableItem } from './timetable'

// 月曆：一格一天，每天列出有哪些課。點課看詳情，點日期換到那天
const props = defineProps<{ month: Date; items: TimetableItem[] }>()
const emit = defineEmits<{ select: [id: string]; day: [date: Date] }>()

// 每格最多列幾堂，其餘顯示「還有 N 堂」
const MAX_PER_DAY = 3
const WEEKDAY_NAMES = ['一', '二', '三', '四', '五', '六', '日']
const today = new Date()

const weeks = computed(() => {
  const first = startOfMonth(props.month)
  const gridStart = startOfWeek(first)
  const nextMonth = new Date(first.getFullYear(), first.getMonth() + 1, 1)
  const rows: Date[][] = []
  for (let start = gridStart; start < nextMonth; start = addDays(start, 7)) {
    rows.push(Array.from({ length: 7 }, (_, index) => addDays(start, index)))
  }
  return rows
})

function itemsOn(day: Date) {
  return props.items
    .filter((item) => sameDay(new Date(item.starts_at), day))
    .sort((a, b) => a.starts_at.localeCompare(b.starts_at))
}

function chipStyle(item: TimetableItem) {
  const palette = lessonColor(item.colorKey)
  return { background: palette.bg, color: palette.ink }
}
</script>

<template>
  <div class="month">
    <div v-for="name in WEEKDAY_NAMES" :key="name" class="month__name">{{ name }}</div>
    <template v-for="week in weeks" :key="week[0]!.toISOString()">
      <div
        v-for="day in week"
        :key="day.toISOString()"
        class="month__cell"
        :class="{ 'month__cell--other': day.getMonth() !== month.getMonth() }"
      >
        <button
          type="button"
          class="month__date"
          :class="{ 'month__date--today': sameDay(day, today) }"
          :aria-label="`${day.getMonth() + 1}月${day.getDate()}日`"
          @click="emit('day', day)"
        >
          {{ day.getDate() }}
        </button>
        <button
          v-for="item in itemsOn(day).slice(0, MAX_PER_DAY)"
          :key="item.id"
          type="button"
          class="month__chip"
          :class="{ 'month__chip--cancelled': item.cancelled }"
          :style="chipStyle(item)"
          :title="item.subtitle ? `${item.title}・${item.subtitle}` : item.title"
          @click="emit('select', item.id)"
        >
          {{ formatTime(item.starts_at) }} {{ item.title }}
        </button>
        <button v-if="itemsOn(day).length > MAX_PER_DAY" type="button" class="month__more" @click="emit('day', day)">
          還有 {{ itemsOn(day).length - MAX_PER_DAY }} 堂
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.month {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  overflow: hidden;
  border: 1px solid var(--home-line);
  border-radius: 22px;
  background: var(--home-paper);
}

.month__name {
  padding: 10px 4px;
  border-bottom: 1px solid var(--home-line);
  color: var(--home-muted);
  font-size: 13px;
  text-align: center;
}

.month__cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  min-height: 104px;
  padding: 6px;
  border-top: 1px solid var(--home-line);
  border-left: 1px solid var(--home-line);
}

.month__cell:nth-child(7n + 1) {
  border-left: 0;
}

.month__cell--other {
  background: var(--home-bg);
}

.month__cell--other .month__date {
  color: var(--home-muted);
}

.month__date {
  align-self: flex-start;
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: none;
  color: var(--home-ink);
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

.month__date:hover {
  background: var(--home-cream);
}

.month__date.month__date--today,
.month__date.month__date--today:hover {
  background: var(--home-accent);
  color: var(--home-paper);
}

.month__chip {
  overflow: hidden;
  padding: 2px 6px;
  border: 0;
  border-radius: 6px;
  font: inherit;
  font-size: 12px;
  line-height: 1.5;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}

.month__chip--cancelled {
  opacity: 0.55;
  text-decoration: line-through;
}

.month__more {
  padding: 0 6px;
  border: 0;
  background: none;
  color: var(--home-muted);
  font: inherit;
  font-size: 12px;
  text-align: left;
  cursor: pointer;
}

@media (max-width: 640px) {
  .month__cell {
    min-height: 72px;
    padding: 4px 2px;
  }

  .month__chip {
    padding: 1px 3px;
    font-size: 11px;
  }
}
</style>
