<script setup lang="ts">
import { computed } from 'vue'
import { addDays, formatTime, sameDay } from '@/utils/format'

export interface TimetableItem {
  id: string
  starts_at: string
  ends_at: string
  title: string
  subtitle?: string
  colorKey: string
  cancelled?: boolean
}

// 一週課表（設計稿 Frame 4／5）：左邊時間，上面星期，課堂依時間畫成色塊
const props = defineProps<{ weekStart: Date; items: TimetableItem[] }>()
const emit = defineEmits<{ select: [id: string] }>()

const HOUR_HEIGHT = 52
const WEEKDAY_NAMES = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
// 暖色系的課程顏色，和首頁的米白、木色同一組
const PALETTE = [
  { bg: '#efe2cf', ink: '#6f5238' },
  { bg: '#e3e6d6', ink: '#55623f' },
  { bg: '#f5dfd2', ink: '#8a4f37' },
  { bg: '#e8dceb', ink: '#5f4a68' },
  { bg: '#dbe6e6', ink: '#3f5c5c' },
]

const days = computed(() => Array.from({ length: 7 }, (_, index) => addDays(props.weekStart, index)))
const today = new Date()

const weekItems = computed(() => {
  const end = addDays(props.weekStart, 7)
  return props.items.filter((item) => {
    const start = new Date(item.starts_at)
    return start >= props.weekStart && start < end
  })
})

// 依這週的課決定要畫幾點到幾點，至少 9:00～21:00
const hours = computed(() => {
  let first = 9
  let last = 21
  for (const item of weekItems.value) {
    first = Math.min(first, new Date(item.starts_at).getHours())
    const end = new Date(item.ends_at)
    last = Math.max(last, end.getHours() + (end.getMinutes() > 0 ? 1 : 0))
  }
  return Array.from({ length: last - first }, (_, index) => first + index)
})

function color(key: string) {
  let hash = 0
  for (const char of key) hash = (hash * 31 + char.charCodeAt(0)) >>> 0
  return PALETTE[hash % PALETTE.length]!
}

function itemsOn(day: Date) {
  return weekItems.value.filter((item) => sameDay(new Date(item.starts_at), day))
}

function blockStyle(item: TimetableItem) {
  const start = new Date(item.starts_at)
  const end = new Date(item.ends_at)
  const firstHour = hours.value[0] ?? 9
  const top = (start.getHours() - firstHour + start.getMinutes() / 60) * HOUR_HEIGHT
  const height = Math.max(((end.getTime() - start.getTime()) / 3_600_000) * HOUR_HEIGHT - 4, 26)
  const palette = color(item.colorKey)
  return { top: `${top}px`, height: `${height}px`, background: palette.bg, color: palette.ink }
}
</script>

<template>
  <div class="week">
    <div class="week__grid" :style="{ '--rows': hours.length, '--hour': `${HOUR_HEIGHT}px` }">
      <div class="week__corner">時間</div>
      <div
        v-for="(day, index) in days"
        :key="day.toISOString()"
        class="week__day"
        :class="{ 'week__day--today': sameDay(day, today) }"
      >
        <span>{{ WEEKDAY_NAMES[index] }}</span>
        <strong>{{ day.getDate() }}</strong>
      </div>

      <div class="week__hours">
        <div v-for="hour in hours" :key="hour" class="week__hour">{{ String(hour).padStart(2, '0') }}:00</div>
      </div>
      <div v-for="day in days" :key="`col-${day.toISOString()}`" class="week__column">
        <button
          v-for="item in itemsOn(day)"
          :key="item.id"
          type="button"
          class="week__block"
          :class="{ 'week__block--cancelled': item.cancelled }"
          :style="blockStyle(item)"
          @click="emit('select', item.id)"
        >
          <strong>{{ item.title }}</strong>
          <span v-if="item.subtitle">{{ item.subtitle }}</span>
          <span>{{ formatTime(item.starts_at) }}－{{ formatTime(item.ends_at) }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.week {
  overflow-x: auto;
  border: 1px solid var(--home-line);
  border-radius: 22px;
  background: var(--home-paper);
}

.week__grid {
  display: grid;
  grid-template-columns: 64px repeat(7, minmax(96px, 1fr));
  grid-template-rows: auto calc(var(--rows) * var(--hour));
  min-width: 760px;
}

.week__corner,
.week__day {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 10px 4px;
  border-bottom: 1px solid var(--home-line);
  color: var(--home-muted);
  font-size: 13px;
}

.week__day strong {
  color: var(--home-ink);
  font-size: 18px;
  font-weight: 500;
}

.week__day--today strong {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--home-accent);
  color: var(--home-paper);
}

.week__hours {
  border-right: 1px solid var(--home-line);
}

.week__hour {
  height: var(--hour);
  padding: 4px 8px 0 0;
  color: var(--home-muted);
  font-size: 12px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.week__column {
  position: relative;
  border-left: 1px solid var(--home-line);
  background-image: linear-gradient(to bottom, var(--home-line) 1px, transparent 1px);
  background-size: 100% var(--hour);
}

.week__column:first-of-type {
  border-left: 0;
}

.week__block {
  position: absolute;
  right: 4px;
  left: 4px;
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 6px 8px;
  overflow: hidden;
  border: 0;
  border-radius: 12px;
  font: inherit;
  font-size: 12px;
  line-height: 1.35;
  text-align: left;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.week__block:hover {
  box-shadow: 0 6px 16px rgba(62, 52, 44, 0.14);
  transform: translateY(-1px);
}

.week__block strong {
  font-size: 13px;
  font-weight: 500;
}

.week__block--cancelled {
  opacity: 0.55;
  text-decoration: line-through;
}
</style>
