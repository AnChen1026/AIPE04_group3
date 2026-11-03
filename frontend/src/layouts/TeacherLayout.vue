<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ConsoleShell, { type NavItem } from '@/components/console/ConsoleShell.vue'
import TeacherApplicationForm from '@/components/console/TeacherApplicationForm.vue'
import { fetchChangeRequests, fetchTeacherConversations } from '@/api/teacher'
import { fetchCurrentUser } from '@/api/auth'
import { fetchSupportConversation } from '@/api/support'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const unread = ref(0)
const pending = ref(0)

// 老師帳號要管理員核准後才能用後台；審核中或沒通過時只顯示狀態
const approved = computed(() => auth.user?.is_active === true)
const status = computed(() => auth.user?.application_status)

// 補填申請後重新讀一次登入資料，畫面換成「審核中」
async function onApplied() {
  auth.setUser(await fetchCurrentUser())
}

// 選單照設計稿：資訊總覽改成點最上方的老師姓名；工作室管理與設定維持原本的頁面
const items = computed<NavItem[]>(() => [
  { to: '/teacher/schedule', label: '課表', icon: 'schedule', badge: pending.value },
  { to: '/teacher/students', label: '學生', icon: 'students' },
  { to: '/teacher/courses', label: '課程', icon: 'courses' },
  { to: '/teacher/practice', label: '作業', icon: 'practice' },
  { to: '/teacher/chat', label: '聊天', icon: 'chat', badge: unread.value },
  { to: '/teacher/studio', label: '工作室管理', icon: 'studio' },
  { to: '/teacher/settings', label: '設定', icon: 'settings' },
])

// 換頁時更新選單上的未讀與待處理數字
async function refreshBadges() {
  if (!approved.value) return
  const [conversations, requests, support] = await Promise.allSettled([
    fetchTeacherConversations(),
    fetchChangeRequests(),
    fetchSupportConversation(),
  ])
  const supportUnread = support.status === 'fulfilled' ? support.value.unread_count : 0
  if (conversations.status === 'fulfilled') {
    unread.value = conversations.value.reduce((sum, row) => sum + row.unread_count, 0) + supportUnread
  }
  if (requests.status === 'fulfilled') pending.value = requests.value.length
}

watch(() => route.fullPath, refreshBadges, { immediate: true })
</script>

<template>
  <ConsoleShell heading="教師管理後台" :items="items" home-to="/teacher" role-label="老師">
    <RouterView v-if="approved" />
    <TeacherApplicationForm v-else-if="!status" @submitted="onApplied" />
    <div v-else class="card pending">
      <h1>{{ status === 'rejected' ? '老師申請沒有通過' : '老師申請審核中' }}</h1>
      <p v-if="status === 'rejected'">
        這次的申請沒有通過。如果想補充資料再申請，請聯絡平台管理員。
      </p>
      <p v-else>平台管理員確認你的資料後，就能開始建立課程、回覆學生洽詢。審核通過後重新整理這一頁即可。</p>
    </div>
  </ConsoleShell>
</template>

<style scoped>
.pending h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 500;
}

.pending p {
  margin: 10px 0 0;
  color: var(--home-muted);
  line-height: 1.8;
}
</style>
