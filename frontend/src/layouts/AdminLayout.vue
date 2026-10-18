<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ConsoleShell, { type NavItem } from '@/components/console/ConsoleShell.vue'
import { fetchApplications } from '@/api/admin'

const route = useRoute()
const pending = ref(0)

const items = computed<NavItem[]>(() => [
  { to: '/admin', label: '資訊總覽', icon: 'overview', exact: true },
  { to: '/admin/applications', label: '老師申請', icon: 'clipboard', badge: pending.value },
  { to: '/admin/teachers', label: '老師', icon: 'students' },
  { to: '/admin/students', label: '學生', icon: 'users' },
])

watch(
  () => route.fullPath,
  async () => {
    const applications = await fetchApplications().catch(() => [])
    pending.value = applications.filter((item) => item.status === 'pending').length
  },
  { immediate: true },
)
</script>

<template>
  <ConsoleShell heading="管理員後台" :items="items">
    <RouterView />
  </ConsoleShell>
</template>
