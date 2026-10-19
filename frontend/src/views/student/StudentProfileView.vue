<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { updateMe } from '@/api/auth'
import { useLeaveGuard } from '@/composables/useLeaveGuard'
import { useAuthStore } from '@/stores/auth'

// 學生自己的基本資料。Email 是登入帳號，這裡不能改。
const auth = useAuthStore()
const form = reactive({
  name: '',
  phone_number: '',
  birthdate: '',
  sex: '' as '' | 'male' | 'female',
})
const original = ref('')
const errors = reactive<Record<string, string>>({})
const serverError = ref('')
const saving = ref(false)
const saved = ref(false)

const dirty = computed(() => original.value !== '' && JSON.stringify(form) !== original.value)
const guard = useLeaveGuard(dirty)

function fill() {
  const user = auth.user
  if (!user) return
  Object.assign(form, {
    name: user.name,
    phone_number: user.phone_number ?? '',
    birthdate: user.birthdate ?? '',
    sex: user.sex === 'male' || user.sex === 'female' ? user.sex : '',
  })
  original.value = JSON.stringify(form)
}

async function save() {
  serverError.value = ''
  for (const key of Object.keys(errors)) delete errors[key]
  if (!form.name.trim()) errors.name = '請填姓名。'
  if (form.phone_number && !/^09\d{8}$/.test(form.phone_number.trim())) errors.phone_number = '手機號碼格式是 09 開頭的 10 碼。'
  if (!form.sex) errors.sex = '請選擇性別。'
  if (Object.keys(errors).length) return

  saving.value = true
  try {
    const user = await updateMe({
      name: form.name.trim(),
      phone_number: form.phone_number.trim() || null,
      birthdate: form.birthdate || null,
      sex: form.sex as 'male' | 'female',
    })
    auth.setUser(user)
    fill()
    saved.value = true
  } catch (problem) {
    serverError.value = problem instanceof Error ? problem.message : '儲存失敗，請稍後再試。'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await auth.ensureLoaded()
  fill()
})
</script>

<template>
  <PageHeader title="基本資料" description="老師在聊天與學生名單看到的是這裡的姓名。">
    <button type="button" class="btn btn--primary" :disabled="saving || !dirty" @click="save">{{ saving ? '儲存中…' : '儲存' }}</button>
  </PageHeader>

  <form class="card" novalidate @submit.prevent="save">
    <div class="form-grid">
      <div class="field field--full">
        <span class="field__label">電子郵件（登入帳號）</span>
        <input class="input" :value="auth.user?.email ?? ''" readonly />
      </div>
      <div class="field">
        <label class="field__label" for="sp-name">姓名<span class="required">*</span></label>
        <input id="sp-name" v-model="form.name" class="input" maxlength="100" autocomplete="name" :aria-invalid="!!errors.name" />
        <p v-if="errors.name" class="error-text">{{ errors.name }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="sp-sex">性別<span class="required">*</span></label>
        <select id="sp-sex" v-model="form.sex" class="select" :aria-invalid="!!errors.sex">
          <option value="" disabled>請選擇</option>
          <option value="female">女</option>
          <option value="male">男</option>
        </select>
        <p v-if="errors.sex" class="error-text">{{ errors.sex }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="sp-phone">手機號碼</label>
        <input id="sp-phone" v-model="form.phone_number" class="input" inputmode="tel" autocomplete="tel" placeholder="0912345678" :aria-invalid="!!errors.phone_number" />
        <p v-if="errors.phone_number" class="error-text">{{ errors.phone_number }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="sp-birthdate">生日</label>
        <input id="sp-birthdate" v-model="form.birthdate" class="input" type="date" />
      </div>
    </div>
    <p v-if="serverError" class="error-text" role="alert">{{ serverError }}</p>
  </form>

  <NoticeDialog :open="saved" message="更新成功！" @confirm="saved = false" @cancel="saved = false" />
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
