<script setup lang="ts">
import { computed } from 'vue'
import { addDays, sameDay } from '@/utils/format'

// 設計稿課表上方的「星期一 19 … 星期日 25」：點一天看當天的課，有課的日子下方有小圓點
const props = defineProps<{ weekStart: Date; marked?: Date[] }>()
const selected = defineModel<Date>({ required: true })

const NAMES = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
const today = new Date()

const days = computed(() =>
  NAMES.map((name, index) => {
    const date = addDays(props.weekStart, index)
    return {
      name,
      date,
      isToday: sameDay(date, today),
      hasLesson: (props.marked ?? []).some((item) => sameDay(item, date)),
    }
  }),
)
</script>

<template>
  <div class="days" role="group" aria-label="選擇日期">
    <button
      v-for="day in days"
      :key="day.name"
      type="button"
      class="day"
      :class="{ 'day--today': day.isToday }"
      :aria-pressed="sameDay(day.date, selected)"
      @click="selected = day.date"
    >
      <span>{{ day.name }}</span>
      <strong>{{ day.date.getDate() }}</strong>
      <i v-if="day.hasLesson" class="day__dot" aria-label="有課"></i>
    </button>
  </div>
</template>

<style scoped>
.days {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 22px;
}

.day {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 4px;
  border: 2px solid var(--home-line);
  border-radius: 22px;
  background: var(--home-paper);
  color: var(--home-ink);
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

.day strong {
  font-size: 18px;
  font-weight: 500;
}

.day--today span,
.day--today strong {
  font-weight: 700;
}

.day[aria-pressed='true'] {
  border-color: var(--home-wood);
  background: var(--home-cream);
}

.day__dot {
  position: absolute;
  bottom: -12px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--home-accent);
}

@media (max-width: 640px) {
  .days {
    gap: 4px;
  }

  .day {
    padding: 8px 2px;
    font-size: 11px;
  }

  .day strong {
    font-size: 15px;
  }
}
</style>
