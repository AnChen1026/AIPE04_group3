<script setup lang="ts">
import { reactive, ref } from 'vue'
import { submitTeacherApplication } from '@/api/auth'
import { ApiError } from '@/api/http'

// 用 Google 註冊的老師還沒有申請資料，在老師後台補填後送管理員審核
const emit = defineEmits<{ submitted: [] }>()

const form = reactive({ teaching_subjects: '', teaching_experience: '', bio: '' })
const proof = ref<File | null>(null)
const error = ref('')
const submitting = ref(false)

function onProof(event: Event) {
  proof.value = (event.target as HTMLInputElement).files?.[0] ?? null
}

async function submit() {
  error.value = ''
  const input = {
    teaching_subjects: form.teaching_subjects.trim(),
    teaching_experience: form.teaching_experience.trim(),
    bio: form.bio.trim(),
  }
  if (!input.teaching_subjects || !input.teaching_experience || !input.bio) {
    error.value = '教學科目、教學經歷和自我介紹都要填。'
    return
  }
  submitting.value = true
  try {
    await submitTeacherApplication(input, proof.value)
    emit('submitted')
  } catch (problem) {
    error.value = problem instanceof ApiError ? problem.message : '送出失敗，請稍後再試。'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form class="card" @submit.prevent="submit">
    <h1 class="card__title">補填老師申請資料</h1>
    <p class="muted">你是用 Google 建立老師帳號的，請補上教學資料。平台管理員審核通過後，就能開始建立課程。</p>
    <div class="field">
      <label class="field__label" for="apply-subjects">教學科目<span class="required">*</span></label>
      <input id="apply-subjects" v-model="form.teaching_subjects" class="input" maxlength="200" />
    </div>
    <div class="field">
      <label class="field__label" for="apply-experience">教學經歷<span class="required">*</span></label>
      <textarea id="apply-experience" v-model="form.teaching_experience" class="textarea" placeholder="例如：教學 5 年，學生從兒童到成人"></textarea>
    </div>
    <div class="field">
      <label class="field__label" for="apply-bio">自我介紹<span class="required">*</span></label>
      <textarea id="apply-bio" v-model="form.bio" class="textarea"></textarea>
    </div>
    <div class="field">
      <label class="field__label" for="apply-proof">證明文件（選填）</label>
      <input id="apply-proof" type="file" accept=".pdf,.jpg,.jpeg,.png" @change="onProof" />
      <span class="field__hint">例如畢業證書或檢定證明，PDF、JPG、PNG。</span>
    </div>
    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    <button type="submit" class="btn btn--primary" :disabled="submitting">
      {{ submitting ? '送出中…' : '送出申請' }}
    </button>
  </form>
</template>
