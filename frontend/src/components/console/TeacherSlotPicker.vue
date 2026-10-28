<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { bookSlot, fetchTeacherAvailability } from '@/api/student'
import type { AvailabilitySlot, ChangeRequest } from '@/types/api'
import { formatDate, formatRange, formatTime } from '@/utils/format'

// 老師還沒被預約的可上課時段，依日期分組。學生點一個時段送出約課，老師完成約課才進正式課表。
// 課程資訊頁和聊天室共用
const props = defineProps<{ courseId: string }>()
const emit = defineEmits<{ booked: [request: ChangeRequest, slot: AvailabilitySlot] }>()

const slots = ref<AvailabilitySlot[]>([])
const loading = ref(false)
const error = ref('')
const notice = ref('')
const picking = ref<AvailabilitySlot | null>(null)
const booking = ref(false)

const days = computed(() => {
  const groups: { label: string; slots: AvailabilitySlot[] }[] = []
  for (const slot of slots.value) {
    const label = formatDate(slot.starts_at)
    const last = groups[groups.length - 1]
    if (last && last.label === label) last.slots.push(slot)
    else groups.push({ label, slots: [slot] })
  }
  return groups
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    slots.value = await fetchTeacherAvailability(props.courseId)
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到老師的時段。'
  } finally {
    loading.value = false
  }
}

async function confirm() {
  const slot = picking.value
  if (!slot) return
  picking.value = null
  booking.value = true
  error.value = ''
  notice.value = ''
  try {
    const request = await bookSlot(props.courseId, slot.id)
    notice.value = `已預約 ${formatRange(slot.starts_at, slot.ends_at)}，等老師完成約課後會出現在課表上。`
    emit('booked', request, slot)
  } catch (problem) {
    // 被別的同學搶先預約時後端回 409，重新整理清單
    error.value = problem instanceof Error ? problem.message : '預約失敗，請再試一次。'
  } finally {
    booking.value = false
    await load()
  }
}

watch(() => props.courseId, load, { immediate: true })
</script>

<template>
  <div class="slots">
    <p v-if="notice" class="slots__notice" role="status">{{ notice }}</p>
    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    <p v-if="loading && slots.length === 0" class="muted">讀取老師的時段中…</p>
    <p v-else-if="slots.length === 0" class="muted">老師目前沒有開放可預約的時段，可以直接在聊天室和老師約時間。</p>
    <div v-for="day in days" :key="day.label" class="slots__day">
      <span class="slots__date">{{ day.label }}</span>
      <div class="slots__list">
        <button
          v-for="slot in day.slots"
          :key="slot.id"
          type="button"
          class="chip"
          :disabled="booking"
          @click="picking = slot"
        >
          {{ formatTime(slot.starts_at) }}－{{ formatTime(slot.ends_at) }}
        </button>
      </div>
    </div>
  </div>

  <NoticeDialog
    :open="picking !== null"
    :message="picking ? `預約 ${formatRange(picking.starts_at, picking.ends_at)}？` : ''"
    detail="送出後這個時段會先保留給你，老師完成約課就會排進課表。"
    confirm-text="預約"
    cancel-text="再想想"
    @confirm="confirm"
    @cancel="picking = null"
  />
</template>

<style scoped>
.slots {
  display: grid;
  gap: 10px;
}

.slots__day {
  display: grid;
  gap: 6px;
}

.slots__date {
  color: var(--home-muted);
  font-size: 13px;
}

.slots__list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.slots__notice {
  margin: 0;
  padding: 10px 14px;
  border-radius: 14px;
  background: var(--home-cream);
  font-size: 14px;
}
</style>
