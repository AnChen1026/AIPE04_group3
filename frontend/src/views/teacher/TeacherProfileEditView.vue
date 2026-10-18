<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { fetchTeacherProfile, saveTeacherProfile } from '@/api/teacher'
import { useLeaveGuard } from '@/composables/useLeaveGuard'
import type { TeacherProfileInput } from '@/types/api'

const CITIES = [
  '台北市', '新北市', '基隆市', '桃園市', '新竹市', '新竹縣', '苗栗縣', '台中市', '彰化縣', '南投縣',
  '雲林縣', '嘉義市', '嘉義縣', '台南市', '高雄市', '屏東縣', '宜蘭縣', '花蓮縣', '台東縣', '澎湖縣', '金門縣', '連江縣',
]

const router = useRouter()
const form = reactive<TeacherProfileInput>({
  name: '',
  gender: '',
  age: 0,
  seniority: 0,
  expertise: '',
  short_intros: '',
  teaching_city: '',
  teaching_district: '',
  target_learning: '',
  teaching_method: '',
  teaching_style: '',
})
const original = ref('')
const errors = reactive<Record<string, string>>({})
const serverError = ref('')
const saving = ref(false)
const saved = ref(false)

const dirty = computed(() => original.value !== '' && JSON.stringify(form) !== original.value)
const guard = useLeaveGuard(dirty)

onMounted(async () => {
  const profile = await fetchTeacherProfile()
  Object.assign(form, {
    name: profile.name,
    gender: profile.gender,
    age: profile.age,
    seniority: profile.seniority,
    expertise: profile.expertise,
    short_intros: profile.short_intros,
    teaching_city: profile.teaching_city,
    teaching_district: profile.teaching_district,
    target_learning: profile.target_learning,
    teaching_method: profile.teaching_method,
    teaching_style: profile.teaching_style,
  })
  original.value = JSON.stringify(form)
})

const textFields: { key: keyof TeacherProfileInput; label: string; max: number }[] = [
  { key: 'expertise', label: '專業', max: 200 },
  { key: 'target_learning', label: '教學對象', max: 255 },
  { key: 'teaching_method', label: '教學方式', max: 255 },
  { key: 'teaching_style', label: '教學風格', max: 100 },
]

function validate() {
  for (const key of Object.keys(errors)) delete errors[key]
  if (!form.name.trim()) errors.name = '請填姓名。'
  if (!form.gender) errors.gender = '請選擇性別。'
  if (!Number.isInteger(form.age) || form.age < 0 || form.age > 120) errors.age = '請填正確的年齡。'
  if (!Number.isInteger(form.seniority) || form.seniority < 0 || form.seniority > 80) errors.seniority = '請填正確的年資。'
  if (!form.teaching_city) errors.teaching_city = '請選擇教學城市。'
  if (!form.teaching_district.trim()) errors.teaching_district = '請填教學地區。'
  for (const field of textFields) {
    const value = String(form[field.key]).trim()
    if (!value) errors[field.key] = `請填${field.label}。`
    else if (value.length > field.max) errors[field.key] = `${field.label}最多 ${field.max} 字。`
  }
  if (!form.short_intros.trim()) errors.short_intros = '請寫一段簡短自我介紹。'
  else if (form.short_intros.length > 200) errors.short_intros = '自我介紹最多 200 字。'
  return Object.keys(errors).length === 0
}

async function save() {
  serverError.value = ''
  if (!validate()) return
  saving.value = true
  try {
    await saveTeacherProfile({ ...form, name: form.name.trim() })
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
    <RouterLink to="/teacher/profile" class="btn btn--ghost">取消</RouterLink>
    <button type="button" class="btn btn--primary" :disabled="saving" @click="save">{{ saving ? '儲存中…' : '儲存' }}</button>
  </PageHeader>

  <form class="card" novalidate @submit.prevent="save">
    <div class="form-grid">
      <div class="field">
        <label class="field__label" for="tp-name">姓名<span class="required">*</span></label>
        <input id="tp-name" v-model="form.name" class="input" :aria-invalid="!!errors.name" />
        <p v-if="errors.name" class="error-text">{{ errors.name }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-gender">性別<span class="required">*</span></label>
        <select id="tp-gender" v-model="form.gender" class="select" :aria-invalid="!!errors.gender">
          <option value="" disabled>請選擇</option>
          <option value="女">女</option>
          <option value="男">男</option>
          <option value="其他">不透露</option>
        </select>
        <p v-if="errors.gender" class="error-text">{{ errors.gender }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-age">年齡<span class="required">*</span></label>
        <input id="tp-age" v-model.number="form.age" class="input" type="number" min="0" :aria-invalid="!!errors.age" />
        <p v-if="errors.age" class="error-text">{{ errors.age }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-seniority">年資（年）<span class="required">*</span></label>
        <input id="tp-seniority" v-model.number="form.seniority" class="input" type="number" min="0" :aria-invalid="!!errors.seniority" />
        <p v-if="errors.seniority" class="error-text">{{ errors.seniority }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-city">教學城市<span class="required">*</span></label>
        <select id="tp-city" v-model="form.teaching_city" class="select" :aria-invalid="!!errors.teaching_city">
          <option value="" disabled>請選擇</option>
          <option v-if="form.teaching_city && !CITIES.includes(form.teaching_city)" :value="form.teaching_city">{{ form.teaching_city }}</option>
          <option v-for="city in CITIES" :key="city" :value="city">{{ city }}</option>
        </select>
        <p v-if="errors.teaching_city" class="error-text">{{ errors.teaching_city }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="tp-district">教學地區<span class="required">*</span></label>
        <input id="tp-district" v-model="form.teaching_district" class="input" placeholder="例如：大安區" :aria-invalid="!!errors.teaching_district" />
        <p v-if="errors.teaching_district" class="error-text">{{ errors.teaching_district }}</p>
      </div>
      <div v-for="field in textFields" :key="field.key" class="field">
        <label class="field__label" :for="`tp-${field.key}`">{{ field.label }}<span class="required">*</span></label>
        <input :id="`tp-${field.key}`" v-model="form[field.key]" class="input" :aria-invalid="!!errors[field.key]" />
        <p v-if="errors[field.key]" class="error-text">{{ errors[field.key] }}</p>
      </div>
      <div class="field field--full">
        <label class="field__label" for="tp-intro">簡短自我介紹<span class="required">*</span></label>
        <textarea id="tp-intro" v-model="form.short_intros" class="textarea" maxlength="200" :aria-invalid="!!errors.short_intros"></textarea>
        <span class="field__hint">{{ form.short_intros.length }} / 200</span>
        <p v-if="errors.short_intros" class="error-text">{{ errors.short_intros }}</p>
      </div>
    </div>
    <p v-if="serverError" class="error-text" role="alert">{{ serverError }}</p>
  </form>

  <NoticeDialog :open="saved" message="更新成功！" @confirm="router.push('/teacher/profile')" @cancel="saved = false" />
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

.error-text {
  font-size: 13px;
}
</style>
