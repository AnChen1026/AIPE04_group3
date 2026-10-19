<script setup lang="ts">
import { ref } from 'vue'
import AuthCard from '@/components/auth/AuthCard.vue'
import AuthField from '@/components/auth/AuthField.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'

// 後端這一輪沒有做「寄送重設連結」（PRD：改密碼、Email 認證留到之後），
// 先保留設計稿的版面，送出時誠實說明目前的處理方式。
const email = ref('')
const error = ref('')
const notice = ref(false)

function submit() {
  error.value = ''
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
    error.value = '請輸入註冊時的電子郵件。'
    return
  }
  notice.value = true
}
</script>

<template>
  <AuthCard eyebrow="RESET" title="忘記密碼？" subtitle="輸入註冊時的電子郵件，我們會協助你重設密碼。">
    <form class="auth-form" novalidate @submit.prevent="submit">
      <AuthField id="forgot-email" v-model="email" label="電子郵件" type="email" inputmode="email" autocomplete="email" placeholder="you@example.com" />
      <p v-if="error" class="auth-alert" role="alert">{{ error }}</p>
      <button type="submit" class="auth-button">寄送重設連結</button>
      <p class="auth-switch">
        想起密碼了？<RouterLink :to="{ name: 'login' }" class="auth-link">立即登入</RouterLink>
      </p>
    </form>

    <NoticeDialog
      :open="notice"
      message="目前還不能線上重設密碼"
      detail="這項功能還在準備中。請聯絡平台管理員，確認身分後協助重設。"
      confirm-text="知道了"
      @confirm="notice = false"
      @cancel="notice = false"
    />
  </AuthCard>
</template>
