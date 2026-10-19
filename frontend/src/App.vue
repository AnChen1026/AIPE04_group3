<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/home/Navbar.vue'
import AiAssistButton from '@/components/common/AiAssistButton.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const route = useRoute()

// 首頁與一般頁面用首頁導覽列；登入頁和後台有自己的版面
const plainLayout = computed(() => !route.meta.layout)
// 登入、註冊等頁共用同一個 AuthLayout，換頁時照片留著，只有右邊表單淡入淡出
const authLayout = computed(() => route.meta.layout === 'auth')

onMounted(() => {
  authStore.loadCurrentUser()
})
</script>

<template>
  <main v-if="authLayout">
    <AuthLayout>
      <RouterView v-slot="{ Component, route: current }">
        <Transition name="auth-swap" mode="out-in">
          <component :is="Component" :key="current.path" />
        </Transition>
      </RouterView>
    </AuthLayout>
  </main>
  <template v-else>
    <Navbar v-if="plainLayout" />
    <main>
      <RouterView />
    </main>
    <AiAssistButton v-if="plainLayout" />
  </template>
</template>

<style>
/* 登入與註冊互相切換：舊表單淡出，新表單由 AuthCard 自己淡入上移 */
.auth-swap-enter-active,
.auth-swap-leave-active {
  transition: opacity 0.28s ease, transform 0.28s ease;
}

.auth-swap-enter-from {
  opacity: 0;
}

.auth-swap-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (prefers-reduced-motion: reduce) {
  .auth-swap-enter-active,
  .auth-swap-leave-active {
    transition: none;
  }
}
</style>
