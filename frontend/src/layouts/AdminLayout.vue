<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ConsoleShell, { type NavItem } from '@/components/console/ConsoleShell.vue'
import { fetchApplications, fetchPasswordResets } from '@/api/admin'
import { fetchAdminConversations } from '@/api/support'

const route = useRoute()
const pending = ref(0)
const resets = ref(0)
const unread = ref(0)

const items = computed<NavItem[]>(() => [
  { to: '/admin', label: '資訊總覽', icon: 'overview', exact: true },
  { to: '/admin/applications', label: '老師申請', icon: 'clipboard', badge: pending.value },
  { to: '/admin/teachers', label: '老師', icon: 'students' },
  { to: '/admin/students', label: '學生', icon: 'users' },
  { to: '/admin/chat', label: '聊天', icon: 'chat', badge: unread.value },
  { to: '/admin/password-resets', label: '重設密碼', icon: 'key', badge: resets.value },
])

async function refreshBadges() {
  const [applications, resetRequests, conversations] = await Promise.all([
    fetchApplications().catch(() => []),
    fetchPasswordResets().catch(() => []),
    fetchAdminConversations().catch(() => []),
  ])
  unread.value = conversations.reduce((sum, row) => sum + row.unread_count, 0)
  pending.value = applications.filter((item) => item.status === 'pending').length
  resets.value = resetRequests.filter((item) => item.status === 'pending').length
}

// 換頁時，以及頁面處理完申請時（admin:refresh-badges 事件）更新選單上的數字
watch(() => route.fullPath, refreshBadges, { immediate: true })
onMounted(() => window.addEventListener('admin:refresh-badges', refreshBadges))
onBeforeUnmount(() => window.removeEventListener('admin:refresh-badges', refreshBadges))
</script>

<template>
  <ConsoleShell heading="管理員後台" :items="items">
    <RouterView />
  </ConsoleShell>
</template>
