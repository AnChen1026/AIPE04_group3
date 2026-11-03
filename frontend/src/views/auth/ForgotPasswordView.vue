<script setup lang="ts">
import { ref } from 'vue'
import AuthCard from '@/components/auth/AuthCard.vue'
import AuthField from '@/components/auth/AuthField.vue'
import { requestPasswordReset } from '@/api/auth'
import { ApiError } from '@/api/http'

// 忘記密碼（地端版本）：還沒有寄信，送出後由管理員在後台重設成臨時密碼，再另外通知使用者。
const email = ref('')
const error = ref('')
const submitting = ref(false)
const sentMessage = ref('')

async function submit() {
  error.value = ''
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
    error.value = '請輸入註冊時的電子郵件。'
    return
  }
  submitting.value = true
  try {
    sentMessage.value = (await requestPasswordReset(email.value.trim())).message
  } catch (problem) {
    error.value = problem instanceof ApiError ? problem.message : '送出失敗，請稍後再試。'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthCard
    eyebrow="RESET"
    title="忘記密碼？"
    :subtitle="sentMessage ? undefined : '輸入註冊時的電子郵件，管理員會協助你重設密碼。'"
  >
    <div v-if="sentMessage" class="auth-form" role="status">
      <p class="forgot__sent">{{ sentMessage }}</p>
      <p class="auth-note">管理員會給你一組臨時密碼。拿到後用它登入，就能繼續使用。</p>
      <RouterLink :to="{ name: 'login' }" class="auth-button">回到登入</RouterLink>
    </div>

    <form v-else class="auth-form" novalidate @submit.prevent="submit">
      <AuthField id="forgot-email" v-model="email" label="電子郵件" type="email" inputmode="email" autocomplete="email" placeholder="you@example.com" />
      <p v-if="error" class="auth-alert" role="alert">{{ error }}</p>
      <button type="submit" class="auth-button" :disabled="submitting">
        {{ submitting ? '送出中…' : '送出重設申請' }}
      </button>
      <p class="auth-switch">
        想起密碼了？<RouterLink :to="{ name: 'login' }" class="auth-link">立即登入</RouterLink>
      </p>
    </form>
  </AuthCard>
</template>

<style scoped>
.forgot__sent {
  margin: 0;
  padding: 16px 18px;
  border-radius: 12px;
  background: var(--home-cream);
  color: var(--home-ink);
  font-size: 14.5px;
  line-height: 1.8;
}
</style>
