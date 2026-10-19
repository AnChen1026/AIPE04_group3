<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthCard from '@/components/auth/AuthCard.vue'
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
  <AuthCard title="建立新帳號" :subtitle="fromContact ? '註冊完成後，會直接帶你到和老師的對話。' : undefined">
    <form novalidate @submit.prevent="submit">
      <p class="signup__label">註冊身分<span class="required">*</span></p>
      <RolePicker v-model="role" student-label="學生" teacher-label="老師" :invalid="!!errors.role" />
      <p v-if="errors.role" class="error-text">{{ errors.role }}</p>

      <div class="field">
        <label class="field__label" for="signup-name">姓名<span class="required">*</span></label>
        <input id="signup-name" v-model="form.name" class="input" autocomplete="name" placeholder="請輸入真實姓名" :aria-invalid="!!errors.name" />
        <p v-if="errors.name" class="error-text">{{ errors.name }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="signup-email">電子郵件<span class="required">*</span></label>
        <input id="signup-email" v-model="form.email" class="input" type="email" autocomplete="email" placeholder="example@email.com" :aria-invalid="!!errors.email" />
        <p v-if="errors.email" class="error-text">{{ errors.email }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="signup-phone">手機號碼<span class="required">*</span></label>
        <input id="signup-phone" v-model="form.phone_number" class="input" inputmode="tel" autocomplete="tel" placeholder="0912345678" :aria-invalid="!!errors.phone_number" />
        <p v-if="errors.phone_number" class="error-text">{{ errors.phone_number }}</p>
      </div>
      <div class="signup__pair">
        <div class="field">
          <label class="field__label" for="signup-birthdate">生日<span class="required">*</span></label>
          <input id="signup-birthdate" v-model="form.birthdate" class="input" type="date" :aria-invalid="!!errors.birthdate" />
          <p v-if="errors.birthdate" class="error-text">{{ errors.birthdate }}</p>
        </div>
        <div class="field">
          <label class="field__label" for="signup-sex">性別<span class="required">*</span></label>
          <select id="signup-sex" v-model="form.sex" class="select" :aria-invalid="!!errors.sex">
            <option value="" disabled>請選擇</option>
            <option value="female">女</option>
            <option value="male">男</option>
          </select>
          <p v-if="errors.sex" class="error-text">{{ errors.sex }}</p>
        </div>
      </div>
      <div class="field">
        <label class="field__label" for="signup-password">設定密碼<span class="required">*</span></label>
        <input id="signup-password" v-model="form.password" class="input" type="password" autocomplete="new-password" placeholder="至少 8 個字元" :aria-invalid="!!errors.password" />
        <p v-if="errors.password" class="error-text">{{ errors.password }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="signup-confirm">確認密碼<span class="required">*</span></label>
        <input id="signup-confirm" v-model="form.password_confirm" class="input" type="password" autocomplete="new-password" placeholder="再次輸入密碼" :aria-invalid="!!errors.password_confirm" />
        <p v-if="errors.password_confirm" class="error-text">{{ errors.password_confirm }}</p>
      </div>

      <template v-if="isTeacher">
        <p class="signup__note">老師帳號要經過平台審核，通過後才能開課。</p>
        <div class="field">
          <label class="field__label" for="signup-subjects">教學科目<span class="required">*</span></label>
          <input id="signup-subjects" v-model="form.teaching_subjects" class="input" :aria-invalid="!!errors.teaching_subjects" />
          <p v-if="errors.teaching_subjects" class="error-text">{{ errors.teaching_subjects }}</p>
        </div>
        <div class="field">
          <label class="field__label" for="signup-experience">教學經歷<span class="required">*</span></label>
          <textarea id="signup-experience" v-model="form.teaching_experience" class="textarea" placeholder="例如：教學 5 年，學生從兒童到成人" :aria-invalid="!!errors.teaching_experience"></textarea>
          <p v-if="errors.teaching_experience" class="error-text">{{ errors.teaching_experience }}</p>
        </div>
        <div class="field">
          <label class="field__label" for="signup-bio">自我介紹<span class="required">*</span></label>
          <textarea id="signup-bio" v-model="form.bio" class="textarea" :aria-invalid="!!errors.bio"></textarea>
          <p v-if="errors.bio" class="error-text">{{ errors.bio }}</p>
        </div>
        <div class="field">
          <label class="field__label" for="signup-proof">證明文件（選填）</label>
          <input id="signup-proof" type="file" accept=".pdf,.jpg,.jpeg,.png" @change="onProof" />
          <span class="field__hint">例如畢業證書或檢定證明，PDF、JPG、PNG。</span>
        </div>
      </template>

      <p class="signup__terms">建立帳號代表您同意服務條款及隱私權政策。</p>
      <p v-if="serverError" class="error-text" role="alert">{{ serverError }}</p>
      <button type="submit" class="btn btn--primary btn--block" :disabled="submitting">
        {{ submitting ? '建立中…' : '建立帳號' }}
      </button>
      <p class="signup__footer">
        已有帳號？<RouterLink :to="{ name: 'login', query: { role: role ?? 'student', redirect: route.query.redirect } }">立即登入</RouterLink>
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
.signup__label {
  margin: 20px 0 0;
  font-size: 14px;
}

.required {
  color: #b5553c;
}

form .field {
  margin-top: 14px;
}

.signup__pair {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.signup__note {
  margin: 18px 0 0;
  padding: 10px 14px;
  border-radius: 14px;
  background: var(--home-cream);
  color: var(--home-accent-dark);
  font-size: 13px;
}

.signup__terms {
  margin: 18px 0 10px;
  color: var(--home-muted);
  font-size: 12px;
}

.signup__footer {
  margin: 16px 0 0;
  color: var(--home-muted);
  font-size: 13px;
  text-align: center;
}

.signup__footer a {
  color: var(--home-accent);
}

.btn--block {
  margin-top: 8px;
}
</style>
