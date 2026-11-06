<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import ImagePicker from '@/components/console/ImagePicker.vue'
import { fetchTeacherProfile, saveTeacherProfile, uploadTeacherPhoto } from '@/api/teacher'
import { fetchCurrentUser } from '@/api/auth'
import { apiUrl } from '@/api/http'
import { useLeaveGuard } from '@/composables/useLeaveGuard'
import { useAuthStore } from '@/stores/auth'
import type { TeacherProfileInput } from '@/types/api'
import defaultPhoto from '@/assets/images/女老師3.png'
import { TAIWAN_CITIES } from '@/utils/format'

// 設定 → 個人資料：帳號資料（姓名、性別、手機、生日）和學生看到的介紹在同一頁（UIUX 回饋），全部必填，照片可不傳。
// 學生看到的性別就是這裡的性別，不另外選；年齡不再填。授課方式、時段等，每門課可以在「課程」裡各自設定。
const router = useRouter()
const auth = useAuthStore()
const form = reactive({
  name: '',
  sex: '' as '' | 'male' | 'female',
  phone_number: '',
  birthdate: '',
  seniority: '' as number | '',
  expertise: '',
  short_intros: '',
  teaching_city: '',
  teaching_district: '',
  target_learning: '',
  teaching_method: '',
  teaching_style: '',
})
const email = ref('')
const photoUrl = ref<string | null>(null)
const photo = ref<File | null>(null)
const original = ref('')
const errors = reactive<Record<string, string>>({})
const serverError = ref('')
const saving = ref(false)
const saved = ref(false)

const dirty = computed(() => photo.value !== null || (original.value !== '' && JSON.stringify(form) !== original.value))
const guard = useLeaveGuard(dirty)

const textFields: { key: 'expertise' | 'target_learning' | 'teaching_method' | 'teaching_style'; label: string; max: number; placeholder: string }[] = [
  { key: 'expertise', label: '專業', max: 200, placeholder: '例如：古典鋼琴、檢定輔導' },
  { key: 'target_learning', label: '教學對象', max: 255, placeholder: '例如：成人初學、兒童' },
  { key: 'teaching_method', label: '教學方式', max: 255, placeholder: '例如：一對一、線上與實體都可' },
  { key: 'teaching_style', label: '教學風格', max: 100, placeholder: '例如：耐心、重視基本功' },
]

onMounted(async () => {
  const profile = await fetchTeacherProfile()
  email.value = profile.email ?? ''
  Object.assign(form, {
    name: profile.name,
    sex: profile.sex === 'male' || profile.sex === 'female' ? profile.sex : '',
    phone_number: profile.phone_number ?? '',
    birthdate: profile.birthdate ?? '',
    seniority: profile.seniority ?? '',
    expertise: profile.expertise ?? '',
    short_intros: profile.short_intros ?? '',
    teaching_city: profile.teaching_city ?? '',
    teaching_district: profile.teaching_district ?? '',
    target_learning: profile.target_learning ?? '',
    teaching_method: profile.teaching_method ?? '',
    teaching_style: profile.teaching_style ?? '',
  })
  photoUrl.value = profile.photo_url ? apiUrl(profile.photo_url) : null
  original.value = JSON.stringify(form)
})

function requiredText(value: string, key: string, message: string) {
  const text = value.trim()
  if (!text) errors[key] = message
  return text
}

async function save() {
  serverError.value = ''
  for (const key of Object.keys(errors)) delete errors[key]
  const name = requiredText(form.name, 'name', '請填姓名。')
  if (!form.sex) errors.sex = '請選擇性別。'
  const phone = form.phone_number.trim()
  if (!/^09\d{8}$/.test(phone)) errors.phone_number = '手機號碼格式是 09 開頭的 10 碼。'
  if (!form.birthdate) errors.birthdate = '請選擇生日。'
  if (form.seniority === '') errors.seniority = '請填教學年資。'
  else if (!Number.isInteger(Number(form.seniority)) || Number(form.seniority) < 0 || Number(form.seniority) > 80) {
    errors.seniority = '教學年資格式不正確。'
  }
  const input: TeacherProfileInput = {
    name,
    sex: form.sex as 'male' | 'female',
    phone_number: phone,
    birthdate: form.birthdate,
    seniority: Number(form.seniority),
    expertise: requiredText(form.expertise, 'expertise', '請填專業。'),
    short_intros: requiredText(form.short_intros, 'short_intros', '請填簡短自我介紹。'),
    teaching_city: requiredText(form.teaching_city, 'teaching_city', '請選擇主要教學城市。'),
    teaching_district: requiredText(form.teaching_district, 'teaching_district', '請填主要教學地區。'),
    target_learning: requiredText(form.target_learning, 'target_learning', '請填教學對象。'),
    teaching_method: requiredText(form.teaching_method, 'teaching_method', '請填教學方式。'),
    teaching_style: requiredText(form.teaching_style, 'teaching_style', '請填教學風格。'),
  }
  for (const field of textFields) {
    if (form[field.key].length > field.max) errors[field.key] = `${field.label}最多 ${field.max} 字。`
  }
  if (Object.keys(errors).length) return

  saving.value = true
  try {
    await saveTeacherProfile(input)
    if (photo.value) {
      const profile = await uploadTeacherPhoto(photo.value)
      photoUrl.value = profile.photo_url ? `${apiUrl(profile.photo_url)}?v=${Date.now()}` : null
      photo.value = null
    }
    // 姓名改了，左側選單和首頁也要跟著變
    auth.setUser(await fetchCurrentUser())
    original.value = JSON.stringify(form)
    saved.value = true
  } catch (problem) {
    serverError.value = problem instanceof Error ? problem.message : '儲存失敗，請稍後再試。'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <PageHeader title="個人資料維護">
    <template #title-actions>
      <RouterLink to="/teacher/settings/profile" class="btn btn--ghost">取消</RouterLink>
      <button type="button" class="btn btn--primary" :disabled="saving" @click="save">{{ saving ? '儲存中…' : '儲存' }}</button>
    </template>
  </PageHeader>

  <form class="card" novalidate @submit.prevent="save">
    <ImagePicker v-model="photo" :current="photoUrl" :fallback="defaultPhoto" label="老師照片" shape="circle" />

    <div class="form-grid profile__grid">
      <div class="field field--full">
        <span class="field__label">電子郵件（登入帳號，不能修改）</span>
        <input class="input" :value="email" readonly />
      </div>
      <div class="field">
        <label class="field__label" for="tp-name">姓名<span class="required">*</span></label>
        <input id="tp-name" v-model="form.name" class="input" maxlength="100" autocomplete="name" :aria-invalid="!!errors.name" />
        <p v-if="errors.name" class="error-text">{{ errors.name }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-sex">性別<span class="required">*</span></label>
        <select id="tp-sex" v-model="form.sex" class="select" :aria-invalid="!!errors.sex">
          <option value="" disabled>請選擇</option>
          <option value="female">女</option>
          <option value="male">男</option>
        </select>
        <p v-if="errors.sex" class="error-text">{{ errors.sex }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-phone">手機號碼<span class="required">*</span></label>
        <input
          id="tp-phone"
          v-model="form.phone_number"
          class="input"
          inputmode="tel"
          autocomplete="tel"
          placeholder="0912345678"
          :aria-invalid="!!errors.phone_number"
        />
        <p v-if="errors.phone_number" class="error-text">{{ errors.phone_number }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-birthdate">生日<span class="required">*</span></label>
        <input id="tp-birthdate" v-model="form.birthdate" class="input" type="date" :aria-invalid="!!errors.birthdate" />
        <p v-if="errors.birthdate" class="error-text">{{ errors.birthdate }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-seniority">教學年資<span class="required">*</span></label>
        <input id="tp-seniority" v-model.number="form.seniority" class="input" type="number" min="0" placeholder="年" :aria-invalid="!!errors.seniority" />
        <p v-if="errors.seniority" class="error-text">{{ errors.seniority }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-city">主要教學城市<span class="required">*</span></label>
        <select id="tp-city" v-model="form.teaching_city" class="select" :aria-invalid="!!errors.teaching_city">
          <option value="" disabled>請選擇</option>
          <option v-if="form.teaching_city && !TAIWAN_CITIES.includes(form.teaching_city)" :value="form.teaching_city">{{ form.teaching_city }}</option>
          <option v-for="city in TAIWAN_CITIES" :key="city" :value="city">{{ city }}</option>
        </select>
        <p v-if="errors.teaching_city" class="error-text">{{ errors.teaching_city }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-district">主要教學地區<span class="required">*</span></label>
        <input
          id="tp-district"
          v-model="form.teaching_district"
          class="input"
          placeholder="例如：大安區"
          maxlength="100"
          :aria-invalid="!!errors.teaching_district"
        />
        <p v-if="errors.teaching_district" class="error-text">{{ errors.teaching_district }}</p>
      </div>
      <div v-for="field in textFields" :key="field.key" class="field">
        <label class="field__label" :for="`tp-${field.key}`">{{ field.label }}<span class="required">*</span></label>
        <input :id="`tp-${field.key}`" v-model="form[field.key]" class="input" :placeholder="field.placeholder" :aria-invalid="!!errors[field.key]" />
        <p v-if="errors[field.key]" class="error-text">{{ errors[field.key] }}</p>
      </div>
      <div class="field field--full">
        <label class="field__label" for="tp-intro">簡短自我介紹<span class="required">*</span></label>
        <textarea id="tp-intro" v-model="form.short_intros" class="textarea" maxlength="200" :aria-invalid="!!errors.short_intros"></textarea>
        <p v-if="errors.short_intros" class="error-text">{{ errors.short_intros }}</p>
        <span class="field__hint">{{ form.short_intros.length }} / 200</span>
      </div>
    </div>
    <p v-if="serverError" class="error-text" role="alert">{{ serverError }}</p>
  </form>

  <NoticeDialog :open="saved" message="更新成功！" @confirm="router.push('/teacher/settings/profile')" @cancel="saved = false" />
  <NoticeDialog
    :open="guard.asking.value"
    message="資料還沒儲存"
    detail="離開這一頁，剛剛修改的內容會不見。"
    confirm-text="不儲存，離開"
    cancel-text="留下來"
    danger
    @confirm="guard.leave"
    @cancel="guard.stay"
  />
</template>

<style scoped>
.required {
  color: #b5553c;
}

.profile__grid {
  margin-top: 22px;
}

.error-text {
  font-size: 13px;
}
</style>
