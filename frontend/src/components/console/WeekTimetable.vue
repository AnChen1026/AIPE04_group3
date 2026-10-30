<script setup lang="ts">
import { computed } from 'vue'
import { addDays, formatTime, sameDay } from '@/utils/format'
import { lessonColor, type TimetableItem } from './timetable'

// 一週課表（設計稿 Frame 4／5）：左邊時間，上面星期，課堂依時間畫成色塊。
// editable 時可以把東西拖到格子或色塊上：drop 帶放下的整點時間與拖曳的資料，色塊上另外帶色塊 id
const props = defineProps<{ weekStart: Date; items: TimetableItem[]; editable?: boolean }>()
const emit = defineEmits<{
  select: [id: string]
  drop: [at: Date, data: string]
  dropOnItem: [id: string, data: string, at: Date]
}>()

const HOUR_HEIGHT = 52
const WEEKDAY_NAMES = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
const days = computed(() => Array.from({ length: 7 }, (_, index) => addDays(props.weekStart, index)))
const today = new Date()

const weekItems = computed(() => {
  const end = addDays(props.weekStart, 7)
  return props.items.filter((item) => {
    const start = new Date(item.starts_at)
    return start >= props.weekStart && start < end
  })
})

// 依這週的課決定要畫幾點到幾點，至少 9:00～21:00；編輯時段時至少 8:00～22:00
const hours = computed(() => {
  let first = props.editable ? 8 : 9
  let last = props.editable ? 22 : 21
  for (const item of weekItems.value) {
    first = Math.min(first, new Date(item.starts_at).getHours())
    const end = new Date(item.ends_at)
    last = Math.max(last, end.getHours() + (end.getMinutes() > 0 ? 1 : 0))
  }
  return Array.from({ length: last - first }, (_, index) => first + index)
})

function itemsOn(day: Date) {
  return weekItems.value.filter((item) => sameDay(new Date(item.starts_at), day))
}

function blockStyle(item: TimetableItem) {
  const start = new Date(item.starts_at)
  const end = new Date(item.ends_at)
  const firstHour = hours.value[0] ?? 9
  const top = (start.getHours() - firstHour + start.getMinutes() / 60) * HOUR_HEIGHT
  const height = Math.max(((end.getTime() - start.getTime()) / 3_600_000) * HOUR_HEIGHT - 4, 26)
  if (item.slot) return { top: `${top}px`, height: `${height}px` }
  const palette = lessonColor(item.colorKey)
  return { top: `${top}px`, height: `${height}px`, background: palette.bg, color: palette.ink }
}

// 拖曳資料都放在 text/plain；放下的位置換成那一欄、那一格的整點
function dropTime(event: DragEvent, day: Date, column: HTMLElement) {
  const offset = event.clientY - column.getBoundingClientRect().top
  const at = new Date(day)
  at.setHours((hours.value[0] ?? 9) + Math.max(0, Math.floor(offset / HOUR_HEIGHT)), 0, 0, 0)
  return at
}

function onColumnDrop(event: DragEvent, day: Date) {
  if (!props.editable) return
  const data = event.dataTransfer?.getData('text/plain')
  if (data) emit('drop', dropTime(event, day, event.currentTarget as HTMLElement), data)
}

function onItemDrop(event: DragEvent, item: TimetableItem, day: Date) {
  if (!props.editable) return
  const data = event.dataTransfer?.getData('text/plain')
  const column = (event.currentTarget as HTMLElement).parentElement
  if (data && column) emit('dropOnItem', item.id, data, dropTime(event, day, column))
}

function onItemDragStart(event: DragEvent, item: TimetableItem) {
  event.dataTransfer?.setData('text/plain', item.id)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function allowDrop(event: DragEvent) {
  if (props.editable) event.preventDefault()
}
</script>

<template>
  <div class="week">
    <div class="week__grid" :class="{ 'week__grid--fit': editable }" :style="{ '--rows': hours.length, '--hour': `${HOUR_HEIGHT}px` }">
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
      <div
        v-for="day in days"
        :key="`col-${day.toISOString()}`"
        class="week__column"
        :class="{ 'week__column--editable': editable }"
        @dragover="allowDrop"
        @drop.prevent="onColumnDrop($event, day)"
      >
        <button
          v-for="item in itemsOn(day)"
          :key="item.id"
          type="button"
          class="week__block"
          :class="{
            'week__block--cancelled': item.cancelled,
            'week__block--open': item.slot === 'open',
            'week__block--held': item.slot === 'held',
          }"
          :style="blockStyle(item)"
          :draggable="editable && item.draggable"
          @click="emit('select', item.id)"
          @dragstart="onItemDragStart($event, item)"
          @dragover="allowDrop"
          @drop.prevent.stop="onItemDrop($event, item, day)"
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

/* 編輯時段時右側多一欄拖曳框，課表縮到容器寬度，不出現橫向捲軸 */
.week__grid--fit {
  grid-template-columns: 52px repeat(7, minmax(0, 1fr));
  min-width: 0;
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

.week__column--editable {
  background-color: color-mix(in srgb, var(--home-cream) 35%, transparent);
}

.week__block--open,
.week__block--held {
  border: 1.5px dashed currentColor;
}

.week__block--open {
  background: #eef3e6;
  color: #55623f;
}

.week__block--held {
  background: #fbefd9;
  color: #8a5a1f;
}

.week__block[draggable='true'] {
  cursor: grab;
}

.week__block--cancelled {
  opacity: 0.55;
  text-decoration: line-through;
}
</style>
