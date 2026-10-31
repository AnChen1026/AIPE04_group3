<script setup lang="ts">
import { computed, watch } from 'vue'
import type { AvailabilitySlot } from '@/types/api'
import { QUARTER_MS, formatDate, formatTime } from '@/utils/format'

// 從老師開放的時段裡選開始時間：先選日期，再選幾點開始。每 15 分鐘一個選項，放不下這堂課長度的不列出。
export interface SlotChoice {
  slot_id: string
  starts_at: string
}

const props = defineProps<{ slots: AvailabilitySlot[]; minutes: number; idPrefix: string }>()
const choice = defineModel<SlotChoice | null>({ required: true })

interface StartOption extends SlotChoice {
  day: string
  label: string
}

const options = computed<StartOption[]>(() => {
  const length = props.minutes * 60_000
  const now = Date.now()
  return props.slots.flatMap((slot) => {
    const list: StartOption[] = []
    const end = new Date(slot.ends_at).getTime()
    let start = Math.ceil(new Date(slot.starts_at).getTime() / QUARTER_MS) * QUARTER_MS
    for (; start + length <= end; start += QUARTER_MS) {
      if (start <= now) continue
      list.push({
        slot_id: slot.id,
        starts_at: new Date(start).toISOString(),
        day: formatDate(new Date(start)),
        label: `${formatTime(new Date(start))}－${formatTime(new Date(start + length))}`,
      })
    }
    return list
  })
})
const days = computed(() => [...new Set(options.value.map((option) => option.day))])

const sameStart = (a: string, b: string) => new Date(a).getTime() === new Date(b).getTime()
const current = computed(() =>
  options.value.find((option) => choice.value && sameStart(option.starts_at, choice.value.starts_at)) ?? null,
)
const dayOptions = computed(() => options.value.filter((option) => option.day === current.value?.day))

function choose(option: StartOption | undefined) {
  choice.value = option ? { slot_id: option.slot_id, starts_at: option.starts_at } : null
}

function chooseDay(day: string) {
  choose(options.value.find((option) => option.day === day))
}

function chooseStart(startsAt: string) {
  choose(dayOptions.value.find((option) => option.starts_at === startsAt))
}

// 換課程、換長度或時段被搶走後，原本選的可能不在了：留在同一天的第一個，否則回到最早的選項
watch(
  options,
  (list) => {
    if (current.value) {
      choose(current.value)
      return
    }
    const day = choice.value ? formatDate(new Date(choice.value.starts_at)) : ''
    const later = choice.value ? list.find((option) => new Date(option.starts_at) >= new Date(choice.value!.starts_at)) : undefined
    choose(list.find((option) => option.day === day) ?? later ?? list[0])
  },
  { immediate: true },
)
</script>

<template>
  <p v-if="options.length === 0" class="muted">老師目前沒有開放放得下這堂課的時段。</p>
  <template v-else>
    <div class="field">
      <label class="field__label" :for="`${idPrefix}-day`">日期</label>
      <select :id="`${idPrefix}-day`" class="select" :value="current?.day" @change="chooseDay(($event.target as HTMLSelectElement).value)">
        <option v-for="day in days" :key="day" :value="day">{{ day }}</option>
      </select>
    </div>
    <div class="field">
      <label class="field__label" :for="`${idPrefix}-start`">時間</label>
      <select
        :id="`${idPrefix}-start`"
        class="select"
        :value="current?.starts_at"
        @change="chooseStart(($event.target as HTMLSelectElement).value)"
      >
        <option v-for="option in dayOptions" :key="option.starts_at" :value="option.starts_at">{{ option.label }}</option>
      </select>
    </div>
  </template>
</template>
