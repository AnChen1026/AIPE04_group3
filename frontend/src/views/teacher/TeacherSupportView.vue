<script setup lang="ts">
import PageHeader from '@/components/console/PageHeader.vue'
import SupportChat from '@/components/console/SupportChat.vue'
import { fetchSupportMessages, sendSupportMessage } from '@/api/support'

// 和平台管理員的對話：審核通過、註冊成功的通知與使用須知都在這裡，有問題也可以直接留言
</script>

<template>
  <PageHeader title="聊天內容">
    <RouterLink to="/teacher/chat" class="btn btn--ghost">返回</RouterLink>
  </PageHeader>
  <SupportChat title="平台管理員" subtitle="通知與使用協助" :load="fetchSupportMessages" :send="sendSupportMessage" />
</template>
