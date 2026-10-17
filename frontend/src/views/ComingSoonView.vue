<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => (route.meta.title as string | undefined) ?? '頁面')
</script>

<template>
  <div class="coming-soon container">
    <h1>{{ title }}</h1>
    <p>這個頁面還在開發中。</p>
    <RouterLink to="/" class="coming-soon__back">回首頁</RouterLink>
  </div>
</template>

<style scoped>
.coming-soon {
  padding-top: 96px;
  padding-bottom: 96px;
  text-align: center;
}

.coming-soon h1 {
  margin: 0 0 12px;
  font-size: 28px;
}

.coming-soon p {
  color: var(--color-text-muted);
}

.coming-soon__back {
  display: inline-block;
  margin-top: 16px;
  padding: 8px 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
}
</style>
