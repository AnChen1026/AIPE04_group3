<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ModalPanel from '@/components/console/ModalPanel.vue'
import { fetchWeeklyAvailability, saveWeeklyAvailability } from '@/api/teacher'
import type { WeeklyWindow } from '@/types/api'
import { QUARTER_OPTIONS, RULE_WEEKDAYS, minuteLabel } from '@/utils/format'

// 老師每週固定可上課的時間，例如每天 18:00-21:00，不用每格手動拉
const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const windows = ref<WeeklyWindow[]>([])
const chosenDays = ref<number[]>([0, 1, 2, 3, 4, 5, 6])
const start = ref(18 * 60)
const end = ref(21 * 60)
const error = ref('')
const saving = ref(false)

const byDay = computed(() =>
  RULE_WEEKDAYS.map((label, weekday) => ({
    label,
    weekday,
    windows: windows.value.filter((item) => item.weekday === weekday).sort((a, b) => a.start_minute - b.start_minute),
  })),
)

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    error.value = ''
    try {
      windows.value = await fetchWeeklyAvailability()
    } catch (problem) {
      error.value = problem instanceof Error ? problem.message : '讀不到固定時間。'
    }
  },
)

// 同一天和新時間重疊的舊時間會被換掉
function addWindows() {
  error.value = ''
  if (end.value <= start.value) {
    error.value = '結束時間要晚於開始時間。'
    return
  }
  if (chosenDays.value.length === 0) {
    error.value = '請至少選一天。'
    return
  }
  const overlaps = (item: WeeklyWindow) =>
    chosenDays.value.includes(item.weekday) && item.start_minute < end.value && item.end_minute > start.value
  windows.value = [
    ...windows.value.filter((item) => !overlaps(item)),
    ...chosenDays.value.map((weekday) => ({ weekday, start_minute: start.value, end_minute: end.value })),
  ]
}

function removeWindow(target: WeeklyWindow) {
  windows.value = windows.value.filter((item) => item !== target)
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    await saveWeeklyAvailability(windows.value)
    emit('saved')
    emit('close')
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '沒有存成功，請再試一次。'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <ModalPanel :open="open" title="設定固定時間" wide @close="emit('close')">
    <p class="muted weekly__hint">
      學生可以從這些時間選擇約課或調課，系統會維持開放未來 8 週。修改後只會重算還沒人預約的時段，已排的課和待確認的預約不會變動。
    </p>
    <fieldset class="weekly__days">
      <legend class="field__label">星期</legend>
      <label v-for="(label, weekday) in RULE_WEEKDAYS" :key="label" class="weekly__day">
        <input v-model="chosenDays" type="checkbox" :value="weekday" />
        {{ label }}
      </label>
    </fieldset>
    <div class="weekly__row">
      <div class="field">
        <label class="field__label" for="weekly-start">開始</label>
        <select id="weekly-start" v-model.number="start" class="select">
          <option v-for="minute in QUARTER_OPTIONS" :key="minute" :value="minute">{{ minuteLabel(minute) }}</option>
        </select>
      </div>
      <div class="field">
        <label class="field__label" for="weekly-end">結束</label>
        <select id="weekly-end" v-model.number="end" class="select">
          <option v-for="minute in QUARTER_OPTIONS" :key="minute" :value="minute">{{ minuteLabel(minute) }}</option>
        </select>
      </div>
      <button type="button" class="btn btn--ghost weekly__add" @click="addWindows">加入</button>
    </div>

    <ul class="weekly__list">
      <li v-for="day in byDay" :key="day.weekday">
        <span class="weekly__label">{{ day.label }}</span>
        <span v-if="day.windows.length === 0" class="muted">不開放</span>
        <button
          v-for="item in day.windows"
          :key="`${item.start_minute}-${item.end_minute}`"
          type="button"
          class="chip"
          :aria-label="`移除${day.label} ${minuteLabel(item.start_minute)} 到 ${minuteLabel(item.end_minute)}`"
          @click="removeWindow(item)"
        >
          {{ minuteLabel(item.start_minute) }}－{{ minuteLabel(item.end_minute) }} ✕
        </button>
      </li>
    </ul>
    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    <template #footer>
      <button type="button" class="btn btn--ghost" @click="emit('close')">取消</button>
      <button type="button" class="btn btn--primary" :disabled="saving" @click="save">{{ saving ? '儲存中…' : '儲存' }}</button>
    </template>
  </ModalPanel>
</template>

<style scoped>
.weekly__hint {
  margin: 0 0 12px;
  font-size: 14px;
}

.weekly__days {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin: 0 0 12px;
  padding: 0;
  border: 0;
}

.weekly__day {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.weekly__row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
}

.weekly__row .field {
  flex: 1 1 120px;
  margin: 0;
}

.weekly__list {
  display: grid;
  gap: 8px;
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
}

.weekly__list li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.weekly__label {
  width: 40px;
  font-weight: 500;
}
</style>
