<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchTeacherProfile } from '@/api/teacher'
import type { TeacherProfile } from '@/types/api'
import { useAuthStore } from '@/stores/auth'

// 設計稿有工作室管理；PRD V1.4 這一輪不做工作室（「有效工作室」不進入本輪），
// 這裡先顯示由後台帶入的基本資訊，欄位都不能修改。
const auth = useAuthStore()
const profile = ref<TeacherProfile | null>(null)

onMounted(async () => {
  profile.value = await fetchTeacherProfile().catch(() => null)
})
</script>

<template>
  <PageHeader title="工作室資訊" description="工作室編號、名稱、擁有者建立後不能自行修改，之後由後台帶入。" />
  <div class="card">
    <div class="form-grid">
      <div class="field">
        <span class="field__label">工作室編號</span>
        <input class="input" :value="profile?.id ?? ''" readonly />
      </div>
      <div class="field">
        <span class="field__label">工作室名稱</span>
        <input class="input" :value="profile ? `${profile.name}鋼琴教室` : ''" readonly />
      </div>
      <div class="field">
        <span class="field__label">工作室擁有者</span>
        <input class="input" :value="auth.user?.name ?? ''" readonly />
      </div>
      <div class="field">
        <span class="field__label">教學地區</span>
        <input class="input" :value="profile ? `${profile.teaching_city}${profile.teaching_district}` : ''" readonly />
      </div>
      <div class="field field--full">
        <span class="field__label">工作室介紹</span>
        <textarea class="textarea" :value="profile?.short_intros ?? ''" readonly></textarea>
      </div>
    </div>
    <p class="studio__note">工作室的建立與多位老師共用，這一輪還沒有開放。目前資料來自你的個人資料，要修改請到「個人資料」。</p>
  </div>
</template>

<style scoped>
.studio__note {
  margin: 18px 0 0;
  padding: 12px 16px;
  border-radius: 16px;
  background: var(--home-cream);
  color: var(--home-accent-dark);
  font-size: 13px;
}
</style>
