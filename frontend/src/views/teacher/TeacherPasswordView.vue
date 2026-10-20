<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { changePassword, fetchCurrentUser } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

// 修改密碼。只用 Google 註冊、還沒有密碼的帳號不用輸入目前密碼，設定後也能用 Email 登入
const auth = useAuthStore()
const form = reactive({ current: '', next: '', confirm: '' })
const errors = reactive<Record<string, string>>({})
const serverError = ref('')
const saving = ref(false)
const done = ref(false)
const shown = ref(false)

const hasPassword = computed(() => auth.user?.has_password !== false)
const inputType = computed(() => (shown.value ? 'text' : 'password'))

async function save() {
  serverError.value = ''
  for (const key of Object.keys(errors)) delete errors[key]
  if (hasPassword.value && !form.current) errors.current = '請輸入目前的密碼。'
  if (form.next.length < 8) errors.next = '新密碼至少 8 個字元。'
  else if (hasPassword.value && form.next === form.current) errors.next = '新密碼不能和目前密碼一樣。'
  if (form.next !== form.confirm) errors.confirm = '兩次輸入的新密碼不一樣。'
  if (Object.keys(errors).length) return

  saving.value = true
  try {
    await changePassword(hasPassword.value ? form.current : null, form.next)
    Object.assign(form, { current: '', next: '', confirm: '' })
    auth.setUser(await fetchCurrentUser())
    done.value = true
  } catch (problem) {
    serverError.value = problem instanceof Error ? problem.message : '密碼沒有更新成功，請稍後再試。'
  } finally {
    saving.value = false
  }
}

onMounted(() => auth.ensureLoaded())
</script>

<template>
  <PageHeader
    title="修改密碼"
    :description="hasPassword ? '新密碼至少 8 個字元。改完之後，下次登入請用新密碼。' : '你是用 Google 建立帳號的，設定密碼後也能用 Email 和密碼登入。'"
  />

  <form class="card password" novalidate @submit.prevent="save">
    <div v-if="hasPassword" class="field">
      <label class="field__label" for="tpw-current">目前密碼<span class="required">*</span></label>
      <input id="tpw-current" v-model="form.current" class="input" :type="inputType" autocomplete="current-password" :aria-invalid="!!errors.current" />
      <p v-if="errors.current" class="error-text">{{ errors.current }}</p>
    </div>
    <div class="field">
      <label class="field__label" for="tpw-next">新密碼<span class="required">*</span></label>
      <input id="tpw-next" v-model="form.next" class="input" :type="inputType" autocomplete="new-password" placeholder="至少 8 個字元" :aria-invalid="!!errors.next" />
      <p v-if="errors.next" class="error-text">{{ errors.next }}</p>
    </div>
    <div class="field">
      <label class="field__label" for="tpw-confirm">確認新密碼<span class="required">*</span></label>
      <input id="tpw-confirm" v-model="form.confirm" class="input" :type="inputType" autocomplete="new-password" placeholder="再輸入一次新密碼" :aria-invalid="!!errors.confirm" />
      <p v-if="errors.confirm" class="error-text">{{ errors.confirm }}</p>
    </div>
    <label class="password__show">
      <input v-model="shown" type="checkbox" />
      顯示密碼
    </label>

    <p v-if="serverError" class="error-text" role="alert">{{ serverError }}</p>
    <div class="password__actions">
      <button type="submit" class="btn btn--primary" :disabled="saving">{{ saving ? '更新中…' : '更新密碼' }}</button>
    </div>
  </form>

  <NoticeDialog :open="done" message="密碼已更新" detail="下次登入請用新密碼。" confirm-text="知道了" @confirm="done = false" @cancel="done = false" />
</template>

<style scoped>
.password {
  max-width: 520px;
}

.password__show {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  color: var(--home-muted);
  font-size: 13px;
  cursor: pointer;
}

.password__actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.required {
  color: #b5553c;
}

.error-text {
  font-size: 13px;
}
</style>
