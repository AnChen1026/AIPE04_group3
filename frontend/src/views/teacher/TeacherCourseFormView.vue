<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import ImagePicker from '@/components/console/ImagePicker.vue'
import { createCourse, fetchCourse, updateCourse, uploadCourseImage } from '@/api/teacher'
import { imageForCourse } from '@/assets/courseImages'
import { apiUrl } from '@/api/http'
import { useLeaveGuard } from '@/composables/useLeaveGuard'
import type { CourseInput } from '@/types/api'
import { COURSE_LEVELS } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const courseId = computed(() => (typeof route.params.id === 'string' ? route.params.id : null))

const form = reactive({
  title: '',
  level: '',
  style: '',
  delivery_mode: '',
  region: '',
  price_per_lesson: '' as string | number,
  time_slots: '',
  description: '',
  status: 'draft' as CourseInput['status'],
})
const imageUrl = ref<string | null>(null)
const image = ref<File | null>(null)
const imagePicker = ref<InstanceType<typeof ImagePicker> | null>(null)
const created = ref(false)
const defaultImage = computed(() => imageForCourse(form.title, form.style))
const original = ref('')
const errors = reactive<Record<string, string>>({})
const serverError = ref('')
const saving = ref(false)
const saved = ref(false)

const dirty = computed(
  () =>
    image.value !== null ||
    (original.value !== '' && JSON.stringify(form) !== original.value),
)
const guard = useLeaveGuard(dirty)

onMounted(async () => {
  if (courseId.value) {
    const course = await fetchCourse(courseId.value)
    Object.assign(form, {
      title: course.title,
      level: course.level ?? '',
      style: course.style ?? '',
      delivery_mode: course.delivery_mode === '線上' ? 'online' : course.delivery_mode === '實體' ? 'in_person' : (course.delivery_mode ?? ''),
      region: course.region ?? '',
      price_per_lesson: course.price_per_lesson ?? '',
      time_slots: course.time_slots ?? '',
      description: course.description ?? '',
      status: course.status,
    })
    imageUrl.value = course.image_url ? apiUrl(course.image_url) : null
  }
  original.value = JSON.stringify(form)
})

function validate() {
  for (const key of Object.keys(errors)) delete errors[key]
  if (!form.title.trim()) errors.title = '請填課程名稱。'
  if (form.price_per_lesson !== '' && (!Number.isInteger(Number(form.price_per_lesson)) || Number(form.price_per_lesson) < 0)) {
    errors.price_per_lesson = '單堂價格要是 0 以上的整數。'
  }
  if (form.status === 'published' && !form.level) errors.level = '發布前請選擇找課程度，學生才找得到。'
  return Object.keys(errors).length === 0
}

function startAnother() {
  created.value = false
  Object.assign(form, {
    title: '',
    level: '',
    style: '',
    delivery_mode: '',
    region: '',
    price_per_lesson: '',
    time_slots: '',
    description: '',
    status: 'draft',
  })
  original.value = JSON.stringify(form)
  imageUrl.value = null
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function save() {
  serverError.value = ''
  if (!validate()) return
  saving.value = true
  const input: CourseInput = {
    title: form.title.trim(),
    level: form.level || null,
    style: form.style.trim() || null,
    delivery_mode: form.delivery_mode || null,
    region: form.region.trim() || null,
    price_per_lesson: form.price_per_lesson === '' ? null : Number(form.price_per_lesson),
    time_slots: form.time_slots.trim() || null,
    description: form.description.trim() || null,
    status: form.status,
  }
  try {
    const course = courseId.value ? await updateCourse(courseId.value, input) : await createCourse(input)
    if (image.value) {
      const updated = await uploadCourseImage(course.id, image.value)
      imageUrl.value = updated.image_url ? `${apiUrl(updated.image_url)}?v=${Date.now()}` : null
      imagePicker.value?.reset()
    }
    original.value = JSON.stringify(form)
    // 新增完回到列表或再新增一門，不會停在剛建立的課程上，避免下一門蓋掉這一門
    if (courseId.value) saved.value = true
    else created.value = true
  } catch (problem) {
    serverError.value = problem instanceof Error ? problem.message : '儲存失敗，請稍後再試。'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <PageHeader :title="courseId ? '課程修改' : '課程新增'">
    <RouterLink to="/teacher/courses" class="btn btn--ghost">回課程列表</RouterLink>
    <button type="button" class="btn btn--primary" :disabled="saving" @click="save">{{ saving ? '儲存中…' : '儲存' }}</button>
  </PageHeader>

  <form class="card" novalidate @submit.prevent="save">
    <ImagePicker
      ref="imagePicker"
      v-model="image"
      :current="imageUrl"
      :fallback="defaultImage"
      label="課程圖片"
      class="course__image"
    />
    <div class="form-grid">
      <div class="field field--full">
        <label class="field__label" for="course-title">課程名稱<span class="required">*</span></label>
        <input id="course-title" v-model="form.title" class="input" maxlength="200" :aria-invalid="!!errors.title" />
        <p v-if="errors.title" class="error-text">{{ errors.title }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="course-style">課程風格</label>
        <input id="course-style" v-model="form.style" class="input" list="course-styles" placeholder="例如：古典鋼琴" maxlength="100" />
        <datalist id="course-styles">
          <option value="古典鋼琴"></option>
          <option value="流行鋼琴"></option>
          <option value="爵士鋼琴"></option>
        </datalist>
      </div>
      <div class="field">
        <label class="field__label" for="course-level">找課程度</label>
        <select id="course-level" v-model="form.level" class="select" :aria-invalid="!!errors.level">
          <option value="">未填</option>
          <option v-for="level in COURSE_LEVELS" :key="level" :value="level">{{ level }}</option>
        </select>
        <p v-if="errors.level" class="error-text">{{ errors.level }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="course-delivery">上課方式</label>
        <select id="course-delivery" v-model="form.delivery_mode" class="select">
          <option value="">未填</option>
          <option value="online">線上</option>
          <option value="in_person">實體</option>
        </select>
      </div>
      <div class="field">
        <label class="field__label" for="course-region">上課地區</label>
        <input id="course-region" v-model="form.region" class="input" placeholder="例如：台北市大安區" maxlength="100" />
      </div>
      <div class="field">
        <label class="field__label" for="course-price">單堂價格（新台幣）</label>
        <input id="course-price" v-model="form.price_per_lesson" class="input" type="number" min="0" step="100" :aria-invalid="!!errors.price_per_lesson" />
        <p v-if="errors.price_per_lesson" class="error-text">{{ errors.price_per_lesson }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="course-slots">可上課時段</label>
        <input id="course-slots" v-model="form.time_slots" class="input" placeholder="例如：週末下午" maxlength="200" />
      </div>
      <div class="field">
        <label class="field__label" for="course-status">課程狀態<span class="required">*</span></label>
        <select id="course-status" v-model="form.status" class="select">
          <option value="draft">草稿（學生看不到）</option>
          <option value="published">已發布</option>
          <option value="archived">已封存</option>
        </select>
      </div>
      <div class="field field--full">
        <label class="field__label" for="course-description">課程介紹</label>
        <textarea
          id="course-description"
          v-model="form.description"
          class="textarea"
          maxlength="2000"
          placeholder="這門課適合誰、會學到什麼、上課怎麼進行"
        ></textarea>
      </div>
    </div>
    <p v-if="serverError" class="error-text" role="alert">{{ serverError }}</p>
  </form>

  <NoticeDialog :open="saved" message="更新成功！" @confirm="saved = false" @cancel="saved = false" />
  <NoticeDialog
    :open="created"
    message="課程已建立！"
    :detail="form.status === 'published' ? '學生已經可以在首頁看到這門課。' : '目前是草稿，發布後學生才看得到。'"
    confirm-text="回課程列表"
    cancel-text="再新增一門"
    @confirm="router.push('/teacher/courses')"
    @cancel="startAnother"
  />
  <NoticeDialog
    :open="guard.asking.value"
    message="課程還沒儲存"
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

.course__image {
  margin-bottom: 22px;
}

.error-text {
  font-size: 13px;
}
</style>
