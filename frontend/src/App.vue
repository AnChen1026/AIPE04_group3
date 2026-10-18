<script setup lang="ts">
import { onMounted } from 'vue'
import Navbar from '@/components/home/Navbar.vue'
import AiAssistButton from '@/components/common/AiAssistButton.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  authStore.loadCurrentUser()
})
</script>

<template>
  <Navbar />
  <main>
    <RouterView />
  </main>
  <AiAssistButton />
</template>
