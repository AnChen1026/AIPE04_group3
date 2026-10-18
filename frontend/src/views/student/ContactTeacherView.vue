<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthCard from '@/components/auth/AuthCard.vue'
import { startConversation } from '@/api/student'
import { ApiError } from '@/api/http'
import { useAuthStore } from '@/stores/auth'

// 首頁課程卡的「聯繫老師」。未登入先登入；學生登入後建立（或打開）這門課的對話。
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const error = ref('')

onMounted(async () => {
  await auth.ensureLoaded()
  if (!auth.user) {
    router.replace({ name: 'login', query: { redirect: route.fullPath, role: 'student' } })
    return
  }
  if (auth.user.role !== 'student') {
    error.value = '請用學生帳號聯繫老師。'
    return
  }
  try {
    const conversation = await startConversation(String(route.params.id))
    router.replace({ name: 'student-chat-room', params: { id: conversation.id } })
  } catch (problem) {
    error.value = problem instanceof ApiError ? problem.message : '暫時無法聯繫老師，請稍後再試。'
  }
})
</script>

<template>
  <AuthCard title="聯繫老師">
    <p v-if="!error" class="contact__text">正在打開和老師的對話…</p>
    <template v-else>
      <p class="error-text contact__text">{{ error }}</p>
      <RouterLink :to="auth.homePath" class="btn btn--ghost btn--block">回到{{ auth.user ? '我的頁面' : '首頁' }}</RouterLink>
    </template>
  </AuthCard>
</template>

<style scoped>
.contact__text {
  margin: 20px 0;
  text-align: center;
}
</style>
