<script setup lang="ts">
import { onMounted } from 'vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import AiAssistButton from '@/components/common/AiAssistButton.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  authStore.loadCurrentUser()
})
</script>

<template>
  <AppHeader />
  <main>
    <RouterView />
  </main>
  <AiAssistButton />
</template>
