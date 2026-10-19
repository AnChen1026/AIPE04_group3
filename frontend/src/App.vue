<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/home/Navbar.vue'
import AiAssistButton from '@/components/common/AiAssistButton.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const route = useRoute()

// 首頁與一般頁面用首頁導覽列；登入頁和後台有自己的版面
const plainLayout = computed(() => !route.meta.layout)

onMounted(() => {
  authStore.loadCurrentUser()
})
</script>

<template>
  <Navbar v-if="plainLayout" />
  <main>
    <RouterView />
  </main>
  <AiAssistButton v-if="plainLayout" />
</template>
