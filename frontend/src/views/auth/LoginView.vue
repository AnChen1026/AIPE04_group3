<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthCard from '@/components/auth/AuthCard.vue'
import AuthField from '@/components/auth/AuthField.vue'
import { fetchGoogleUrl } from '@/api/auth'
import { ApiError } from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { safeRedirect } from '@/utils/redirect'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

// 登入不需要先選身分：後端依帳號的角色決定登入後去哪裡。網址帶的 role 只用來預選註冊身分
const role = route.query.role === 'teacher' ? 'teacher' : 'student'
const email = ref('')
const password = ref('')
// Google 驗證失敗時，後端導回登入頁並在網址帶 error
const error = ref(typeof route.query.error === 'string' ? route.query.error : '')
const submitting = ref(false)

function nextPath(userRole: string) {
  return safeRedirect(route.query.redirect, userRole, auth.homePath)
}

async function submit() {
  error.value = ''
  if (!email.value.trim() || !password.value) {
    error.value = '請輸入電子郵件和密碼。'
    return
  }
  submitting.value = true
  try {
    const user = await auth.login(email.value.trim(), password.value)
    router.replace(nextPath(user.role))
  } catch (problem) {
    error.value = problem instanceof ApiError ? problem.message : '登入失敗，請稍後再試。'
  } finally {
    submitting.value = false
  }
}

async function googleLogin() {
  error.value = ''
  try {
    const { url } = await fetchGoogleUrl(role, 'login')
    window.location.href = url
  } catch (problem) {
    error.value = problem instanceof ApiError ? problem.message : '暫時無法使用 Google 登入。'
  }
}
</script>

<template>
  <AuthCard eyebrow="LOG IN" title="歡迎回來" subtitle="登入後，繼續你的課程與練習。">
    <form class="auth-form" novalidate @submit.prevent="submit">
      <AuthField id="login-email" v-model="email" label="電子郵件" type="email" autocomplete="email" inputmode="email" placeholder="you@example.com" />
      <div>
        <AuthField id="login-password" v-model="password" label="密碼" type="password" autocomplete="current-password" placeholder="請輸入密碼" />
        <div class="login__forgot">
          <RouterLink to="/forgot-password" class="auth-link">忘記密碼？</RouterLink>
        </div>
      </div>

      <p v-if="error" class="auth-alert" role="alert">{{ error }}</p>

      <button type="submit" class="auth-button" :disabled="submitting">
        {{ submitting ? '登入中…' : '確認登入' }}
      </button>

      <p class="auth-divider">或</p>

      <button type="button" class="auth-button auth-button--ghost" @click="googleLogin">
        <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
          <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.6l6.7-6.7C35.6 2.5 30.2 0 24 0 14.6 0 6.6 5.4 2.7 13.3l7.8 6C12.4 13.6 17.7 9.5 24 9.5z" />
          <path fill="#4285F4" d="M46.1 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.4c-.5 2.9-2.2 5.3-4.6 6.9l7.3 5.7c4.3-4 7-9.9 7-17.1z" />
          <path fill="#FBBC05" d="M10.5 28.7A14.5 14.5 0 0 1 9.5 24c0-1.6.3-3.2.8-4.7l-7.8-6A24 24 0 0 0 0 24c0 3.9.9 7.5 2.6 10.7l7.9-6z" />
          <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.3-5.7c-2 1.4-4.7 2.3-8.6 2.3-6.3 0-11.6-4.1-13.5-9.8l-7.9 6C6.6 42.6 14.6 48 24 48z" />
        </svg>
        使用 Google 登入
      </button>

      <p class="auth-switch">
        還沒有帳號？
        <RouterLink :to="{ name: 'signup', query: { role, redirect: route.query.redirect } }" class="auth-link">立即註冊</RouterLink>
      </p>
    </form>
  </AuthCard>
</template>

<style scoped>
.login__forgot {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}
</style>
