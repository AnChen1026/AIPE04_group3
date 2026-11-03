<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import ChatPanel from '@/components/console/ChatPanel.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { fetchTeacherConversation, fetchTeacherMessages, issueBindingCode, sendTeacherMessage } from '@/api/teacher'
import { useConversation } from '@/composables/useConversation'
import { useAuthStore } from '@/stores/auth'
import type { Conversation } from '@/types/api'

const route = useRoute()
const auth = useAuthStore()
const conversationId = String(route.params.id)
const conversation = ref<Conversation | null>(null)
const chat = useConversation({ load: fetchTeacherMessages, send: sendTeacherMessage, myId: () => auth.user?.id ?? '' })
const asking = ref(false)
const issuing = ref(false)
const actionError = ref('')

async function refreshInfo() {
  conversation.value = await fetchTeacherConversation(conversationId)
}

async function send(body: string) {
  try {
    await chat.send(body, auth.user!.id)
  } catch (problem) {
    actionError.value = problem instanceof Error ? problem.message : '訊息沒有送出。'
  }
}

// 綁定碼會當成一則訊息貼進對話，學生在自己的聊天頁輸入後就進入這門課
async function issueCode() {
  asking.value = false
  issuing.value = true
  actionError.value = ''
  try {
    await issueBindingCode(conversationId)
    await Promise.all([chat.reload(), refreshInfo()])
  } catch (problem) {
    actionError.value = problem instanceof Error ? problem.message : '綁定碼沒有產生成功。'
  } finally {
    issuing.value = false
  }
}

onMounted(async () => {
  await Promise.all([refreshInfo().catch(() => undefined), chat.open(conversationId)])
})
</script>

<template>

  <ChatPanel
    :title="`學生：${conversation?.student_name ?? ''}`"
    :subtitle="conversation ? `${conversation.course_title}${conversation.course_level ? `・${conversation.course_level}` : ''}` : ''"
    :messages="chat.messages.value"
    :my-id="auth.user?.id ?? ''"
    :loading="chat.loading.value"
    :error="chat.error.value"
    :connected="chat.connected.value"
    @send="send"
  >
    <template #actions>
      <div class="chat-actions">
        <template v-if="conversation?.bound">
          <span class="badge badge--accent">已綁定</span>
          <span class="muted">這位學生已經進入這門課。</span>
        </template>
        <template v-else>
          <span v-if="conversation?.binding_code" class="muted">
            已發綁定碼 <code class="chat-code">{{ conversation.binding_code }}</code>，學生還沒使用。
          </span>
          <span v-else class="muted">決定收這位學生時，發一組只屬於他、這門課的綁定碼。</span>
          <button type="button" class="btn btn--primary btn--small" :disabled="issuing" @click="asking = true">
            {{ issuing ? '產生中…' : conversation?.binding_code ? '重發綁定碼' : '發綁定碼' }}
          </button>
        </template>
      </div>
      <p v-if="actionError" class="error-text" role="alert">{{ actionError }}</p>
    </template>
  </ChatPanel>

  <NoticeDialog
    :open="asking"
    message="發送綁定碼？"
    detail="綁定碼會貼進這段對話。如果之前發過還沒用的碼，舊的會失效。"
    confirm-text="發送"
    cancel-text="取消"
    @confirm="issueCode"
    @cancel="asking = false"
  />
</template>

<style scoped>
.chat-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 14px;
}

.chat-actions .btn {
  margin-left: auto;
}

.chat-code {
  padding: 2px 8px;
  border-radius: 8px;
  background: var(--home-cream);
  color: var(--home-accent-dark);
  letter-spacing: 0.1em;
}
</style>
