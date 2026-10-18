<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ConsoleShell, { type NavItem } from '@/components/console/ConsoleShell.vue'
import { fetchMyConversations } from '@/api/student'

const route = useRoute()
const unread = ref(0)

// 學生專區沿用老師後台的版面：我的課程（含聊天）、課表、練習
const items = computed<NavItem[]>(() => [
  { to: '/student', label: '我的課程', icon: 'home', exact: true, badge: unread.value },
  { to: '/student/schedule', label: '課表', icon: 'schedule' },
  { to: '/student/practice', label: '練習', icon: 'mic' },
  { to: '/student/profile', label: '基本資料', icon: 'profile' },
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
  <ConsoleShell heading="學生專區" :items="items">
    <RouterView />
  </ConsoleShell>
</template>
