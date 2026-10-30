<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import ChatPanel from '@/components/console/ChatPanel.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import TeacherSlotPicker from '@/components/console/TeacherSlotPicker.vue'
import { fetchMyConversation, fetchStudentMessages, redeemBindingCode, sendStudentMessage } from '@/api/student'
import { useConversation } from '@/composables/useConversation'
import { useAuthStore } from '@/stores/auth'
import type { AvailabilitySlot, Conversation } from '@/types/api'
import { formatRange } from '@/utils/format'

const route = useRoute()
const auth = useAuthStore()
const conversationId = String(route.params.id)
const conversation = ref<Conversation | null>(null)
const chat = useConversation({ load: fetchStudentMessages, send: sendStudentMessage, myId: () => auth.user?.id ?? '' })
const code = ref('')
const binding = ref(false)
const bindError = ref('')
const bound = ref(false)
const panel = ref<InstanceType<typeof ChatPanel> | null>(null)
// 「查看老師時段」：在訊息下方由系統列出老師可預約的時段，點一下就能預約
const showSlots = ref(false)

async function toggleSlots() {
  showSlots.value = !showSlots.value
  if (showSlots.value) await panel.value?.scrollToEnd()
}

// 預約後在對話裡留一句話，老師在聊天室也看得到
async function onBooked(_request: unknown, slot: AvailabilitySlot) {
  await send(`我預約了 ${formatRange(slot.starts_at, slot.ends_at)} 的時段，請老師完成約課。`)
}

async function refreshInfo() {
  conversation.value = await fetchMyConversation(conversationId)
}

async function send(body: string) {
  try {
    await chat.send(body, auth.user!.id)
  } catch (problem) {
    bindError.value = problem instanceof Error ? problem.message : '訊息沒有送出。'
  }
}

async function bind() {
  bindError.value = ''
  if (!code.value.trim()) {
    bindError.value = '請輸入老師給你的綁定碼。'
    return
  }
  binding.value = true
  try {
    await redeemBindingCode(conversationId, code.value.trim().toUpperCase())
    code.value = ''
    bound.value = true
    await refreshInfo()
  } catch (problem) {
    bindError.value = problem instanceof Error ? problem.message : '綁定失敗，請確認綁定碼。'
  } finally {
    binding.value = false
  }
}

onMounted(async () => {
  await Promise.all([refreshInfo().catch(() => undefined), chat.open(conversationId)])
})
</script>

<template>

  <ChatPanel
    ref="panel"
    :title="conversation ? `${conversation.teacher_name} 老師` : ''"
    :subtitle="conversation?.course_title ?? ''"
    :messages="chat.messages.value"
    :my-id="auth.user?.id ?? ''"
    :loading="chat.loading.value"
    :error="chat.error.value"
    :connected="chat.connected.value"
    @send="send"
  >
    <template #actions>
      <div v-if="conversation?.bound" class="chat-actions">
        <span class="badge badge--accent">上課中</span>
        <button type="button" class="btn btn--ghost btn--small" :aria-pressed="showSlots" @click="toggleSlots">
          {{ showSlots ? '收起老師時段' : '查看老師時段' }}
        </button>
        <RouterLink :to="{ path: '/student/schedule', query: { course: conversation.course_id } }" class="btn btn--ghost btn--small">課表</RouterLink>
        <RouterLink to="/student/homework" class="btn btn--primary btn--small">看作業</RouterLink>
      </div>
      <form v-else class="chat-actions" @submit.prevent="bind">
        <label class="muted" for="bind-code">老師給你綁定碼了嗎？</label>
        <input id="bind-code" v-model="code" class="input bind__input" placeholder="輸入綁定碼" autocomplete="off" />
        <button type="submit" class="btn btn--primary btn--small" :disabled="binding">{{ binding ? '確認中…' : '進入課程' }}</button>
      </form>
      <p v-if="bindError" class="error-text" role="alert">{{ bindError }}</p>
    </template>
    <template v-if="showSlots && conversation?.bound" #after>
      <div class="slot-message">
        <p class="slot-message__title">系統：{{ conversation.teacher_name }} 老師目前可以上課的時段，點一個就能預約</p>
        <TeacherSlotPicker :course-id="conversation.course_id" @booked="onBooked" />
      </div>
    </template>
  </ChatPanel>

  <NoticeDialog
    :open="bound"
    message="已經進入這門課！"
    detail="現在可以看課表、請假或調課，也能照老師指定的曲子錄音練習。"
    @confirm="bound = false"
    @cancel="bound = false"
  />
</template>

<style scoped>
.chat-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 14px;
}

.slot-message {
  align-self: center;
  width: min(520px, 100%);
  margin: 6px auto;
  padding: 14px 16px;
  border: 1px dashed var(--home-line);
  border-radius: 18px;
  background: var(--home-paper);
}

.slot-message__title {
  margin: 0 0 10px;
  color: var(--home-muted);
  font-size: 13px;
}

.bind__input {
  width: 160px;
  min-height: 34px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
</style>
