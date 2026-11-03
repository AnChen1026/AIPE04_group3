<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { fetchStudio, fetchTeacherProfile, saveStudio } from '@/api/teacher'
import { useAuthStore } from '@/stores/auth'
import type { Studio } from '@/types/api'
import { TAIWAN_CITIES } from '@/utils/format'

// 工作室資料：審核通過後由老師自己填寫。編號由系統在第一次儲存時產生、之後不變，其他欄位都可以改。
// 還沒建立時，先用老師的姓名與教學地區帶入預設值
const auth = useAuthStore()
const studio = ref<Studio | null>(null)
const loaded = ref(false)
const form = reactive({ name: '', owner_name: '', city: '', district: '', intro: '' })
const errors = reactive<Record<string, string>>({})
const serverError = ref('')
const saving = ref(false)
const saved = ref('')

function fill(value: Studio) {
  studio.value = value
  Object.assign(form, {
    name: value.name,
    owner_name: value.owner_name,
    city: value.city ?? '',
    district: value.district ?? '',
    intro: value.intro ?? '',
  })
}

async function save() {
  for (const key of Object.keys(errors)) delete errors[key]
  serverError.value = ''
  if (!form.name.trim()) errors.name = '請填寫工作室名稱。'
  if (!form.owner_name.trim()) errors.owner_name = '請填寫工作室擁有者。'
  if (Object.keys(errors).length) return
  const creating = !studio.value
  saving.value = true
  try {
    fill(
      await saveStudio({
        name: form.name.trim(),
        owner_name: form.owner_name.trim(),
        city: form.city || null,
        district: form.district.trim() || null,
        intro: form.intro.trim() || null,
      }),
    )
    saved.value = creating ? `工作室已建立！編號是 ${studio.value!.code}。` : '已儲存！'
  } catch (problem) {
    serverError.value = problem instanceof Error ? problem.message : '工作室資料沒有儲存成功。'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const current = await fetchStudio()
    if (current) fill(current)
    else {
      const profile = await fetchTeacherProfile().catch(() => null)
      form.owner_name = auth.user?.name ?? ''
      form.city = profile?.teaching_city ?? ''
      form.district = profile?.teaching_district ?? ''
    }
  } catch (problem) {
    serverError.value = problem instanceof Error ? problem.message : '讀不到工作室資料。'
  } finally {
    loaded.value = true
  }
})
</script>

<template>
  <PageHeader
    title="工作室資訊"
    :description="studio ? '工作室編號由系統產生、不能修改，其他資料隨時可以更新。' : '還沒有工作室資料。填好按「建立工作室」，系統會產生工作室編號。'"
  >
    <button type="submit" form="studio-form" class="btn btn--primary" :disabled="saving || !loaded">
      {{ saving ? '儲存中…' : studio ? '儲存' : '建立工作室' }}
    </button>
  </PageHeader>

  <form v-if="loaded" id="studio-form" class="card" novalidate @submit.prevent="save">
    <div class="form-grid">
      <div class="field">
        <label class="field__label" for="studio-code">工作室編號</label>
        <input id="studio-code" class="input" :value="studio?.code ?? ''" placeholder="建立後由系統產生" readonly />
      </div>
      <div class="field">
        <label class="field__label" for="studio-name">工作室名稱</label>
        <input
          id="studio-name"
          v-model="form.name"
          class="input"
          maxlength="100"
          placeholder="例如：晨光鋼琴教室"
          :aria-invalid="Boolean(errors.name)"
        />
        <p v-if="errors.name" class="error-text">{{ errors.name }}</p>
      </div>
      <div class="field">
        <label class="field__label" for="studio-owner">工作室擁有者</label>
        <input id="studio-owner" v-model="form.owner_name" class="input" maxlength="100" :aria-invalid="Boolean(errors.owner_name)" />
        <p v-if="errors.owner_name" class="error-text">{{ errors.owner_name }}</p>
      </div>
      <div class="field">
        <span class="field__label">教學地區</span>
        <div class="studio__area">
          <label class="visually-hidden" for="studio-city">縣市</label>
          <select id="studio-city" v-model="form.city" class="select">
            <option value="">選擇縣市</option>
            <option v-if="form.city && !TAIWAN_CITIES.includes(form.city)" :value="form.city">{{ form.city }}</option>
            <option v-for="city in TAIWAN_CITIES" :key="city" :value="city">{{ city }}</option>
          </select>
          <label class="visually-hidden" for="studio-district">區</label>
          <input id="studio-district" v-model="form.district" class="input" maxlength="100" placeholder="例如：大安區" />
        </div>
      </div>
      <div class="field field--full">
        <label class="field__label" for="studio-intro">工作室介紹</label>
        <textarea
          id="studio-intro"
          v-model="form.intro"
          class="textarea"
          maxlength="1000"
          placeholder="教學理念、上課環境、適合的學生…"
        ></textarea>
      </div>
    </div>
    <p v-if="serverError" class="error-text" role="alert">{{ serverError }}</p>
  </form>

  <NoticeDialog :open="Boolean(saved)" :message="saved" @confirm="saved = ''" @cancel="saved = ''" />
</template>

<style scoped>
.studio__area {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 10px;
}
</style>
