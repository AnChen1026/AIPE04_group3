<script setup lang="ts">
import SupportChat from '@/components/console/SupportChat.vue'
import { fetchSupportMessages, sendSupportMessage } from '@/api/support'

// 和平台管理員的對話：審核通過、註冊成功的通知與使用須知都在這裡，有問題也可以直接留言
</script>

<template>
  <SupportChat title="平台管理員" subtitle="通知與使用協助" :load="fetchSupportMessages" :send="sendSupportMessage" />
</template>
