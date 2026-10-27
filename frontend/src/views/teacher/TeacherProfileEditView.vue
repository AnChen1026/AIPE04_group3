<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import ImagePicker from '@/components/console/ImagePicker.vue'
import { fetchTeacherProfile, saveTeacherProfile, uploadTeacherPhoto } from '@/api/teacher'
import { apiUrl } from '@/api/http'
import { useLeaveGuard } from '@/composables/useLeaveGuard'
import { useAuthStore } from '@/stores/auth'
import type { TeacherProfileInput } from '@/types/api'
import defaultPhoto from '@/assets/images/女老師3.png'
import { TAIWAN_CITIES } from '@/utils/format'

// 只有姓名、性別必填。授課方式、地區、時段等，每門課可以在「課程」裡各自設定。
const router = useRouter()
const auth = useAuthStore()
const form = reactive({
  name: '',
  gender: '',
  age: '' as number | '',
  seniority: '' as number | '',
  expertise: '',
  short_intros: '',
  teaching_city: '',
  teaching_district: '',
  target_learning: '',
  teaching_method: '',
  teaching_style: '',
})
const photoUrl = ref<string | null>(null)
const photo = ref<File | null>(null)
const original = ref('')
const errors = reactive<Record<string, string>>({})
const serverError = ref('')
const saving = ref(false)
const saved = ref(false)

const dirty = computed(() => photo.value !== null || (original.value !== '' && JSON.stringify(form) !== original.value))
const guard = useLeaveGuard(dirty)

const textFields: { key: keyof typeof form; label: string; max: number; placeholder: string }[] = [
  { key: 'expertise', label: '專業', max: 200, placeholder: '例如：古典鋼琴、檢定輔導' },
  { key: 'target_learning', label: '教學對象', max: 255, placeholder: '例如：成人初學、兒童' },
  { key: 'teaching_method', label: '教學方式', max: 255, placeholder: '例如：一對一、線上與實體都可' },
  { key: 'teaching_style', label: '教學風格', max: 100, placeholder: '例如：耐心、重視基本功' },
]

onMounted(async () => {
  const [profile] = await Promise.all([fetchTeacherProfile(), auth.ensureLoaded()])
  Object.assign(form, {
    // 姓名以帳號的基本資料為準（課程頁顯示的就是它），在「基本資料」修改
    name: auth.user?.name ?? profile.name,
    gender: profile.gender === '未填寫' ? '' : profile.gender,
    age: profile.age ?? '',
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

function numberOrNull(value: number | '', max: number, key: string, label: string) {
  if (value === '') return null
  if (!Number.isInteger(Number(value)) || Number(value) < 0 || Number(value) > max) {
    errors[key] = `${label}格式不正確。`
  }
  return Number(value)
}

function textOrNull(value: string) {
  return value.trim() || null
}

async function save() {
  serverError.value = ''
  for (const key of Object.keys(errors)) delete errors[key]
  if (!form.name.trim()) errors.name = '請填姓名。'
  if (!form.gender) errors.gender = '請選擇性別。'
  const input: TeacherProfileInput = {
    name: form.name.trim(),
    gender: form.gender,
    age: numberOrNull(form.age, 120, 'age', '年齡'),
    seniority: numberOrNull(form.seniority, 80, 'seniority', '年資'),
    expertise: textOrNull(form.expertise),
    short_intros: textOrNull(form.short_intros),
    teaching_city: textOrNull(form.teaching_city),
    teaching_district: textOrNull(form.teaching_district),
    target_learning: textOrNull(form.target_learning),
    teaching_method: textOrNull(form.teaching_method),
    teaching_style: textOrNull(form.teaching_style),
  }
  for (const field of textFields) {
    if (String(form[field.key]).length > field.max) errors[field.key] = `${field.label}最多 ${field.max} 字。`
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
  <PageHeader title="個人資料維護" description="只有姓名、性別必填。授課方式、地區、時段可以在每門課裡各自設定。">
    <RouterLink to="/teacher/settings/profile" class="btn btn--ghost">取消</RouterLink>
    <button type="button" class="btn btn--primary" :disabled="saving" @click="save">{{ saving ? '儲存中…' : '儲存' }}</button>
  </PageHeader>

  <form class="card" novalidate @submit.prevent="save">
    <ImagePicker v-model="photo" :current="photoUrl" :fallback="defaultPhoto" label="老師照片" shape="circle" />

    <div class="form-grid profile__grid">
      <div class="field">
        <label class="field__label" for="tp-name">姓名</label>
        <input id="tp-name" :value="form.name" class="input" readonly />
        <span class="field__hint">姓名在 <RouterLink to="/teacher/settings/account" class="profile__link">基本資料</RouterLink> 修改，課程頁會一起更新。</span>
      </div>
      <div class="field">
        <label class="field__label" for="tp-gender">對學生顯示的性別<span class="required">*</span></label>
        <select id="tp-gender" v-model="form.gender" class="select" :aria-invalid="!!errors.gender">
          <option value="" disabled>請選擇</option>
          <option value="女">女</option>
          <option value="男">男</option>
          <option value="不透露">不透露</option>
        </select>
        <p v-if="errors.gender" class="error-text">{{ errors.gender }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-age">年齡（選填）</label>
        <input id="tp-age" v-model.number="form.age" class="input" type="number" min="0" :aria-invalid="!!errors.age" />
        <p v-if="errors.age" class="error-text">{{ errors.age }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-seniority">教學年資（選填）</label>
        <input id="tp-seniority" v-model.number="form.seniority" class="input" type="number" min="0" placeholder="年" :aria-invalid="!!errors.seniority" />
        <p v-if="errors.seniority" class="error-text">{{ errors.seniority }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-city">主要教學城市（選填）</label>
        <select id="tp-city" v-model="form.teaching_city" class="select">
          <option value="">不指定</option>
          <option v-if="form.teaching_city && !TAIWAN_CITIES.includes(form.teaching_city)" :value="form.teaching_city">{{ form.teaching_city }}</option>
          <option v-for="city in TAIWAN_CITIES" :key="city" :value="city">{{ city }}</option>
        </select>
      </div>
      <div class="field">
        <label class="field__label" for="tp-district">主要教學地區（選填）</label>
        <input id="tp-district" v-model="form.teaching_district" class="input" placeholder="例如：大安區" maxlength="100" />
      </div>
      <div v-for="field in textFields" :key="field.key" class="field">
        <label class="field__label" :for="`tp-${field.key}`">{{ field.label }}（選填）</label>
        <input :id="`tp-${field.key}`" v-model="form[field.key]" class="input" :placeholder="field.placeholder" :aria-invalid="!!errors[field.key]" />
        <p v-if="errors[field.key]" class="error-text">{{ errors[field.key] }}</p>
      </div>
      <div class="field field--full">
        <label class="field__label" for="tp-intro">簡短自我介紹（選填）</label>
        <textarea id="tp-intro" v-model="form.short_intros" class="textarea" maxlength="200"></textarea>
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
.profile__link {
  color: var(--home-accent);
  text-decoration: underline;
  text-underline-offset: 3px;
}

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
