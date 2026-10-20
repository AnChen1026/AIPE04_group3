<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthCard from '@/components/auth/AuthCard.vue'
import AuthField from '@/components/auth/AuthField.vue'
import RolePicker from '@/components/auth/RolePicker.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { registerStudent, registerTeacher } from '@/api/auth'
import { ApiError } from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { safeRedirect } from '@/utils/redirect'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const role = ref<'student' | 'teacher' | null>(
  route.query.role === 'teacher' ? 'teacher' : route.query.role === 'student' ? 'student' : null,
)
const form = reactive({
  name: '',
  email: '',
  phone_number: '',
  birthdate: '',
  sex: '' as '' | 'male' | 'female',
  password: '',
  password_confirm: '',
  teaching_subjects: '鋼琴',
  teaching_experience: '',
  bio: '',
})
const proof = ref<File | null>(null)
const errors = reactive<Record<string, string>>({})
const serverError = ref('')
const submitting = ref(false)
const done = ref(false)

const isTeacher = computed(() => role.value === 'teacher')
const fromContact = computed(() => String(route.query.redirect ?? '').includes('/contact'))

// 設計稿的「錯誤提示：哪欄資料有誤、沒有選擇身分」
function validate(): boolean {
  for (const key of Object.keys(errors)) delete errors[key]
  if (!role.value) errors.role = '請先選擇註冊身分。'
  if (!form.name.trim()) errors.name = '請輸入真實姓名。'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) errors.email = '請輸入正確的電子郵件。'
  if (!/^09\d{8}$/.test(form.phone_number.trim())) errors.phone_number = '請輸入手機號碼，例如 0912345678。'
  if (!form.birthdate) errors.birthdate = '請選擇生日。'
  if (!form.sex) errors.sex = '請選擇性別。'
  if (form.password.length < 8) errors.password = '密碼至少 8 個字元。'
  if (form.password !== form.password_confirm) errors.password_confirm = '兩次輸入的密碼不一樣。'
  if (isTeacher.value) {
    if (!form.teaching_subjects.trim()) errors.teaching_subjects = '請填教學科目。'
    if (!form.teaching_experience.trim()) errors.teaching_experience = '請簡單說明教學經歷。'
    if (!form.bio.trim()) errors.bio = '請寫一段自我介紹。'
  }
  return Object.keys(errors).length === 0
}

async function submit() {
  serverError.value = ''
  if (!validate()) return
  submitting.value = true
  const base = {
    email: form.email.trim(),
    password: form.password,
    name: form.name.trim(),
    phone_number: form.phone_number.trim(),
    birthdate: form.birthdate,
    sex: form.sex as 'male' | 'female',
  }
  try {
    if (isTeacher.value) {
      await registerTeacher(
        {
          ...base,
          password_confirm: form.password_confirm,
          teaching_subjects: form.teaching_subjects.trim(),
          teaching_experience: form.teaching_experience.trim(),
          bio: form.bio.trim(),
        },
        proof.value,
      )
      done.value = true
    } else {
      // 學生註冊完直接登入，從「與老師接洽」來的就直接打開聊天
      await registerStudent(base)
      await auth.login(base.email, base.password)
      router.replace(safeRedirect(route.query.redirect, 'student', '/student'))
    }
  } catch (problem) {
    serverError.value = problem instanceof ApiError ? problem.message : '註冊失敗，請稍後再試。'
  } finally {
    submitting.value = false
  }
}

function onProof(event: Event) {
  proof.value = (event.target as HTMLInputElement).files?.[0] ?? null
}

function finish() {
  router.push({ name: 'login', query: { role: role.value ?? 'student' } })
}
</script>

<template>
  <AuthCard
    eyebrow="SIGN UP"
    title="建立帳號"
    :subtitle="fromContact ? '註冊完成後，會直接帶你到和老師的對話。' : '幾個步驟，就能開始找老師，或開設自己的鋼琴課。'"
  >
    <form class="auth-form" novalidate @submit.prevent="submit">
      <div class="auth-field">
        <p class="auth-field__label" id="signup-role-label">註冊身分<span class="auth-field__required" aria-hidden="true">*</span></p>
        <RolePicker
          v-model="role"
          student-label="我是學生"
          teacher-label="我是老師"
          student-hint="找老師、上課與練習"
          teacher-hint="開課與管理學生"
          :invalid="!!errors.role"
        />
        <p v-if="errors.role" class="auth-field__error">{{ errors.role }}</p>
      </div>

      <AuthField id="signup-name" v-model="form.name" label="姓名" autocomplete="name" placeholder="請輸入真實姓名" :maxlength="100" required :error="errors.name" />
      <AuthField id="signup-email" v-model="form.email" label="電子郵件" type="email" inputmode="email" autocomplete="email" placeholder="you@example.com" required :error="errors.email" />
      <AuthField id="signup-password" v-model="form.password" label="密碼" type="password" autocomplete="new-password" placeholder="至少 8 個字元" required :error="errors.password" />
      <AuthField id="signup-confirm" v-model="form.password_confirm" label="確認密碼" type="password" autocomplete="new-password" placeholder="再輸入一次密碼" required :error="errors.password_confirm" />

      <p class="auth-section-title">基本資料</p>
      <AuthField id="signup-phone" v-model="form.phone_number" label="手機號碼" inputmode="tel" autocomplete="tel" placeholder="0912345678" required :error="errors.phone_number" />
      <div class="auth-pair">
        <AuthField id="signup-birthdate" label="生日" required :error="errors.birthdate">
          <input id="signup-birthdate" v-model="form.birthdate" class="auth-input" type="date" :aria-invalid="!!errors.birthdate || undefined" />
        </AuthField>
        <AuthField id="signup-sex" label="性別" required :error="errors.sex">
          <select id="signup-sex" v-model="form.sex" class="auth-input" required :aria-invalid="!!errors.sex || undefined">
            <option value="" disabled>請選擇</option>
            <option value="female">女</option>
            <option value="male">男</option>
          </select>
        </AuthField>
      </div>

      <Transition name="signup-teacher">
        <div v-if="isTeacher" class="signup__teacher">
          <p class="auth-section-title">教學資料</p>
          <p class="auth-note">老師帳號送出後由平台審核，通過後就能開課。</p>
          <AuthField id="signup-subjects" v-model="form.teaching_subjects" label="教學科目" :maxlength="200" required :error="errors.teaching_subjects" />
          <AuthField id="signup-experience" label="教學經歷" required :error="errors.teaching_experience">
            <textarea id="signup-experience" v-model="form.teaching_experience" class="auth-input" rows="2" placeholder="例如：教學 5 年，學生從兒童到成人" :aria-invalid="!!errors.teaching_experience || undefined"></textarea>
          </AuthField>
          <AuthField id="signup-bio" label="自我介紹" required :error="errors.bio">
            <textarea id="signup-bio" v-model="form.bio" class="auth-input" rows="2" :aria-invalid="!!errors.bio || undefined"></textarea>
          </AuthField>
          <AuthField id="signup-proof" label="證明文件（選填）" hint="例如畢業證書或檢定證明，PDF、JPG、PNG。">
            <input id="signup-proof" class="signup__file" type="file" accept=".pdf,.jpg,.jpeg,.png" @change="onProof" />
          </AuthField>
        </div>
      </Transition>

      <p v-if="serverError" class="auth-alert" role="alert">{{ serverError }}</p>

      <button type="submit" class="auth-button" :disabled="submitting">
        {{ submitting ? '建立中…' : '建立帳號' }}
      </button>
      <p class="auth-note signup__terms">建立帳號代表你同意服務條款及隱私權政策。</p>

      <p class="auth-switch">
        已經有帳號？
        <RouterLink :to="{ name: 'login', query: { role: role ?? 'student', redirect: route.query.redirect } }" class="auth-link">立即登入</RouterLink>
      </p>
    </form>

    <NoticeDialog
      :open="done"
      message="註冊成功！"
      detail="老師帳號送出審核，通過後就能開課。現在可以先登入查看審核狀態。"
      confirm-text="前往登入"
      @confirm="finish"
      @cancel="finish"
    />
  </AuthCard>
</template>

<style scoped>
.signup__teacher {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.signup__file {
  width: 100%;
  padding: 10px 0;
  color: var(--home-muted);
  font-size: 13px;
}

.signup__file::file-selector-button {
  margin-right: 12px;
  padding: 6px 14px;
  border: 1px solid var(--home-wood);
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--home-ink);
  font: inherit;
  cursor: pointer;
}

.signup__terms {
  margin-top: -6px;
  text-align: center;
}

.signup-teacher-enter-active,
.signup-teacher-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.signup-teacher-enter-from,
.signup-teacher-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (prefers-reduced-motion: reduce) {
  .signup-teacher-enter-active,
  .signup-teacher-leave-active {
    transition: none;
  }
}
</style>
