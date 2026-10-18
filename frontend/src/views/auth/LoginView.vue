<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthCard from '@/components/auth/AuthCard.vue'
import RolePicker from '@/components/auth/RolePicker.vue'
import { fetchGoogleUrl } from '@/api/auth'
import { ApiError } from '@/api/http'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const role = ref<'student' | 'teacher' | null>(route.query.role === 'teacher' ? 'teacher' : 'student')
const email = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

function nextPath(userRole: string) {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
  // 只回到站內頁面，而且要是這個身分能進的地方
  if (redirect.startsWith('/') && !redirect.startsWith('//')) {
    if (redirect.startsWith('/teacher') && userRole !== 'teacher') return auth.homePath
    if (redirect.startsWith('/student') && userRole !== 'student') return auth.homePath
    return redirect
  }
  return auth.homePath
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
    const { url } = await fetchGoogleUrl(role.value ?? 'student', 'login')
    window.location.href = url
  } catch (problem) {
    error.value = problem instanceof ApiError ? problem.message : '暫時無法使用 Google 登入。'
  }
}
</script>

<template>
  <AuthCard subtitle="歡迎回來，請先選擇登入身分">
    <RolePicker
      v-model="role"
      student-label="學生登入"
      teacher-label="老師登入"
      student-hint="查看課程及學習進度"
      teacher-hint="管理學生與課程"
    />

    <form class="login" novalidate @submit.prevent="submit">
      <div class="field">
        <label class="field__label" for="login-email">電子郵件</label>
        <input id="login-email" v-model="email" class="input" type="email" autocomplete="email" placeholder="請輸入電子郵件" />
      </div>
      <div class="field">
        <label class="field__label" for="login-password">密碼</label>
        <input
          id="login-password"
          v-model="password"
          class="input"
          type="password"
          autocomplete="current-password"
          placeholder="請輸入密碼"
        />
      </div>
      <div class="login__row">
        <RouterLink to="/forgot-password" class="login__link">忘記密碼？</RouterLink>
      </div>

      <p v-if="error" class="error-text" role="alert">{{ error }}</p>

      <button type="submit" class="btn btn--primary btn--block" :disabled="submitting">
        {{ submitting ? '登入中…' : '確認登入' }}
      </button>
      <button type="button" class="btn btn--ghost btn--block" @click="googleLogin">
        <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
          <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.6l6.7-6.7C35.6 2.5 30.2 0 24 0 14.6 0 6.6 5.4 2.7 13.3l7.8 6C12.4 13.6 17.7 9.5 24 9.5z" />
          <path fill="#4285F4" d="M46.1 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.4c-.5 2.9-2.2 5.3-4.6 6.9l7.3 5.7c4.3-4 7-9.9 7-17.1z" />
          <path fill="#FBBC05" d="M10.5 28.7A14.5 14.5 0 0 1 9.5 24c0-1.6.3-3.2.8-4.7l-7.8-6A24 24 0 0 0 0 24c0 3.9.9 7.5 2.6 10.7l7.9-6z" />
          <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.3-5.7c-2 1.4-4.7 2.3-8.6 2.3-6.3 0-11.6-4.1-13.5-9.8l-7.9 6C6.6 42.6 14.6 48 24 48z" />
        </svg>
        Google 登入
      </button>

      <p class="login__footer">
        還沒有帳號？
        <RouterLink :to="{ name: 'signup', query: { role: role ?? 'student' } }" class="login__link">立即註冊</RouterLink>
      </p>
    </form>
  </AuthCard>
</template>

<style scoped>
.login {
  margin-top: 18px;
}

.login .btn--block {
  margin-top: 12px;
}

.login__row {
  display: flex;
  justify-content: flex-end;
  margin: 10px 0 4px;
}

.login__link {
  color: var(--home-accent);
  font-size: 13px;
}

.login__link:hover {
  text-decoration: underline;
}

.login__footer {
  margin: 18px 0 0;
  color: var(--home-muted);
  font-size: 13px;
  text-align: center;
}

.error-text {
  margin-top: 10px;
}
</style>
