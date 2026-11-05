<script setup lang="ts">
import { computed, ref } from 'vue'
import { addDays, formatTime, sameDay } from '@/utils/format'
import { lessonColor, type TimetableItem } from './timetable'

// 一週課表（設計稿 Frame 4／5）：左邊時間，上面星期，課堂依時間畫成色塊。
// editable 時可以把東西拖到格子或色塊上：drop 帶放下的時間（對齊 15 分鐘）與拖曳的資料，色塊上另外帶色塊 id
const props = defineProps<{ weekStart: Date; items: TimetableItem[]; editable?: boolean }>()
const emit = defineEmits<{
  select: [id: string]
  drop: [at: Date, data: string]
  dropOnItem: [id: string, data: string, at: Date]
  resize: [id: string, endsAt: Date]
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

// 拉長、縮短時段：按住底部把手上下拖，結束時間以 15 分鐘為單位，
// 最短 15 分鐘，最長到當天下一個框的開頭（沒有就到午夜）。放開才送出
const QUARTER = 15 * 60_000
const resizing = ref<{ id: string; startY: number; originalEnd: number; min: number; max: number; end: number } | null>(null)

function endOf(item: TimetableItem) {
  return resizing.value?.id === item.id ? new Date(resizing.value.end) : new Date(item.ends_at)
}

function startResize(event: PointerEvent, item: TimetableItem, day: Date) {
  const start = new Date(item.starts_at).getTime()
  const midnight = addDays(new Date(day.getFullYear(), day.getMonth(), day.getDate()), 1).getTime()
  const nextStart = itemsOn(day)
    .map((other) => new Date(other.starts_at).getTime())
    .filter((time) => time > start)
  const originalEnd = new Date(item.ends_at).getTime()
  resizing.value = {
    id: item.id,
    startY: event.clientY,
    originalEnd,
    min: start + QUARTER,
    max: Math.min(midnight, ...nextStart),
    end: originalEnd,
  }
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

function moveResize(event: PointerEvent) {
  const state = resizing.value
  if (!state) return
  const quarters = Math.round((event.clientY - state.startY) / (HOUR_HEIGHT / 4))
  state.end = Math.min(state.max, Math.max(state.min, state.originalEnd + quarters * QUARTER))
}

function endResize() {
  const state = resizing.value
  resizing.value = null
  if (state && state.end !== state.originalEnd) emit('resize', state.id, new Date(state.end))
}

function blockStyle(item: TimetableItem) {
  const start = new Date(item.starts_at)
  const end = endOf(item)
  const firstHour = hours.value[0] ?? 9
  const top = (start.getHours() - firstHour + start.getMinutes() / 60) * HOUR_HEIGHT
  const height = Math.max(((end.getTime() - start.getTime()) / 3_600_000) * HOUR_HEIGHT - 4, 26)
  if (item.slot) return { top: `${top}px`, height: `${height}px` }
  const palette = lessonColor(item.colorKey)
  return { top: `${top}px`, height: `${height}px`, background: palette.bg, color: palette.ink }
}

// 拖曳資料都放在 text/plain；放下的位置換成那一欄的時間，以 15 分鐘為單位
function dropTime(event: DragEvent, day: Date, column: HTMLElement) {
  const offset = event.clientY - column.getBoundingClientRect().top
  const at = new Date(day)
  const quarters = Math.max(0, Math.floor(offset / (HOUR_HEIGHT / 4)))
  at.setHours(hours.value[0] ?? 9, quarters * 15, 0, 0)
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
  if (resizing.value) {
    event.preventDefault()
    return
  }
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
            'week__block--resizing': resizing?.id === item.id,
          }"
          :style="blockStyle(item)"
          :draggable="editable && item.draggable && !resizing"
          @click="emit('select', item.id)"
          @dragstart="onItemDragStart($event, item)"
          @dragover="allowDrop"
          @drop.prevent.stop="onItemDrop($event, item, day)"
        >
          <strong>{{ item.title }}</strong>
          <span v-if="item.subtitle">{{ item.subtitle }}</span>
          <span>{{ formatTime(item.starts_at) }}－{{ formatTime(endOf(item).toISOString()) }}</span>
          <span
            v-if="editable && item.resizable"
            class="week__resize"
            title="上下拖動調整結束時間"
            draggable="false"
            @pointerdown.stop.prevent="startResize($event, item, day)"
            @pointermove="moveResize"
            @pointerup="endResize"
            @pointercancel="resizing = null"
            @click.stop
          />
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

/* 編輯時多畫淡淡的 15 分鐘線，拖放時看得出會落在哪裡 */
.week__column--editable {
  background-color: color-mix(in srgb, var(--home-cream) 35%, transparent);
  background-image:
    linear-gradient(to bottom, var(--home-line) 1px, transparent 1px),
    linear-gradient(to bottom, color-mix(in srgb, var(--home-line) 45%, transparent) 1px, transparent 1px);
  background-size: 100% var(--hour), 100% calc(var(--hour) / 4);
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

/* 底部的把手：滑過時出現一條短線，上下拖動改結束時間 */
.week__resize {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 10px;
  cursor: ns-resize;
  touch-action: none;
}

.week__resize::after {
  position: absolute;
  bottom: 3px;
  left: 50%;
  width: 28px;
  height: 3px;
  border-radius: 2px;
  background: currentColor;
  opacity: 0;
  transform: translateX(-50%);
  transition: opacity 0.15s ease;
  content: '';
}

.week__block:hover .week__resize::after,
.week__block--resizing .week__resize::after {
  opacity: 0.6;
}

.week__block--resizing {
  z-index: 2;
  box-shadow: 0 6px 16px rgba(62, 52, 44, 0.14);
  transition: none;
}

.week__block--cancelled {
  opacity: 0.55;
  text-decoration: line-through;
}
</style>
