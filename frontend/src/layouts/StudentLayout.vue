<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ConsoleShell, { type NavItem } from '@/components/console/ConsoleShell.vue'
import { fetchMyConversations } from '@/api/student'

const route = useRoute()
const unread = ref(0)

// 學生專區沿用老師後台的版面，選單照設計稿；資訊總覽是點最上方的學生姓名
const items = computed<NavItem[]>(() => [
  { to: '/student/schedule', label: '課表', icon: 'schedule' },
  { to: '/student/teachers', label: '老師', icon: 'students' },
  { to: '/student/courses', label: '課程', icon: 'courses' },
  { to: '/student/homework', label: '作業', icon: 'practice' },
  { to: '/student/chat', label: '聊天', icon: 'chat', badge: unread.value },
  { to: '/student/settings', label: '設定', icon: 'settings' },
])

watch(
  () => route.fullPath,
  async () => {
    const conversations = await fetchMyConversations().catch(() => [])
    unread.value = conversations.reduce((sum, row) => sum + row.unread_count, 0)
  },
  { immediate: true },
)
</script>

<template>
  <ConsoleShell heading="學生課程與學習管理平台" :items="items" home-to="/student" role-label="學生">
    <RouterView />
  </ConsoleShell>
</template>
