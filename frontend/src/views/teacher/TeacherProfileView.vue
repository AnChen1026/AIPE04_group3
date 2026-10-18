<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchTeacherProfile } from '@/api/teacher'
import type { TeacherProfile } from '@/types/api'
import { apiUrl } from '@/api/http'
import defaultPhoto from '@/assets/images/女老師3.png'

const profile = ref<TeacherProfile | null>(null)
const error = ref('')

const rows: { key: keyof TeacherProfile; label: string; suffix?: string }[] = [
  { key: 'name', label: '姓名' },
  { key: 'gender', label: '性別' },
  { key: 'age', label: '年齡', suffix: ' 歲' },
  { key: 'seniority', label: '年資', suffix: ' 年' },
  { key: 'expertise', label: '專業' },
  { key: 'teaching_city', label: '教學城市' },
  { key: 'teaching_district', label: '教學地區' },
  { key: 'target_learning', label: '教學對象' },
  { key: 'teaching_method', label: '教學方式' },
  { key: 'teaching_style', label: '教學風格' },
  { key: 'short_intros', label: '簡短自我介紹' },
]

onMounted(async () => {
  try {
    profile.value = await fetchTeacherProfile()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到個人資料。'
  }
})
</script>

<template>
  <PageHeader title="個人資料" description="學生在課程頁看到的老師介紹。">
    <RouterLink to="/teacher/profile/edit" class="btn btn--primary">編輯</RouterLink>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>
  <div v-if="profile" class="card profile__head">
    <img :src="profile.photo_url ? apiUrl(profile.photo_url) : defaultPhoto" :alt="`${profile.name}的照片`" />
    <div>
      <strong>{{ profile.name }}</strong>
      <span class="muted">{{ profile.photo_url ? '學生在課程頁會看到這張照片。' : '還沒上傳照片，目前顯示預設圖。' }}</span>
    </div>
  </div>
  <dl v-if="profile" class="card profile">
    <div v-for="row in rows" :key="row.key" class="profile__row">
      <dt>{{ row.label }}</dt>
      <dd :class="{ muted: profile[row.key] === '' || profile[row.key] === null }">
        {{ profile[row.key] === '' || profile[row.key] === null ? '未填' : `${profile[row.key]}${row.suffix ?? ''}` }}
      </dd>
    </div>
  </dl>
</template>

<style scoped>
.profile {
  margin: 0;
}

.profile__head {
  display: flex;
  align-items: center;
  gap: 18px;
}

.profile__head img {
  width: 84px;
  height: 84px;
  object-fit: cover;
  object-position: center 20%;
  border-radius: 50%;
}

.profile__head div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profile__head strong {
  font-family: var(--font-serif);
  font-size: 20px;
}

.profile__head span {
  font-size: 13px;
}

.profile__row {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr);
  gap: 16px;
  padding: 12px 0;
  border-top: 1px solid var(--home-line);
}

.profile__row:first-child {
  border-top: 0;
}

.profile dt {
  color: var(--home-muted);
  font-size: 14px;
}

.profile dd {
  margin: 0;
  white-space: pre-wrap;
}

@media (max-width: 560px) {
  .profile__row {
    grid-template-columns: 1fr;
    gap: 2px;
  }
}
</style>
