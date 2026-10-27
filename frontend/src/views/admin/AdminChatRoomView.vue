<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import SupportChat from '@/components/console/SupportChat.vue'
import { fetchAdminConversation, fetchAdminMessages, sendAdminMessage } from '@/api/support'
import type { SupportConversation } from '@/types/api'

const route = useRoute()
const conversationId = String(route.params.id)
const conversation = ref<SupportConversation | null>(null)

const load = () => fetchAdminMessages(conversationId)
const send = (body: string, clientMessageId: string) => sendAdminMessage(conversationId, body, clientMessageId)

onMounted(async () => {
  conversation.value = await fetchAdminConversation(conversationId).catch(() => null)
})
</script>

<template>
  <SupportChat
    v-if="conversation"
    :title="conversation.user_name"
    :subtitle="conversation.user_role === 'teacher' ? '老師' : '學生'"
    :owner-id="conversation.user_id"
    :load="load"
    :send="send"
  />
</template>
