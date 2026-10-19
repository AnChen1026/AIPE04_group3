<script setup lang="ts">
import { ref } from 'vue'
import AuthCard from '@/components/auth/AuthCard.vue'
import RolePicker from '@/components/auth/RolePicker.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'

// 後端這一輪沒有做「寄送重設連結」（PRD：改密碼、Email 認證留到之後），
// 先保留設計稿的版面，送出時誠實說明目前的處理方式。
const role = ref<'student' | 'teacher' | null>('student')
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
  <AuthCard title="忘記密碼？" subtitle="輸入您的電子郵件，我們會協助您重設密碼。">
    <RolePicker v-model="role" student-label="我是學生" teacher-label="我是老師" />
    <form novalidate @submit.prevent="submit">
      <div class="field">
        <label class="field__label" for="forgot-email">電子郵件</label>
        <input id="forgot-email" v-model="email" class="input" type="email" autocomplete="email" placeholder="請輸入電子郵件" />
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <button type="submit" class="btn btn--primary btn--block">寄送重設連結</button>
      <p class="forgot__footer">
        想起密碼了？<RouterLink :to="{ name: 'login', query: { role: role ?? 'student' } }">立即登入</RouterLink>
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

<style scoped>
form {
  margin-top: 16px;
}

.btn--block {
  margin-top: 18px;
}

.error-text {
  margin-top: 8px;
}

.forgot__footer {
  margin: 16px 0 0;
  color: var(--home-muted);
  font-size: 13px;
  text-align: center;
}

.forgot__footer a {
  color: var(--home-accent);
}
</style>
