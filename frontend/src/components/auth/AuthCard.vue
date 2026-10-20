<script setup lang="ts">
// 登入、註冊、忘記密碼、聯繫老師右側表單的標題區與內容。左右分割的外框在 layouts/AuthLayout.vue
defineProps<{ title?: string; subtitle?: string; eyebrow?: string }>()
</script>

<template>
  <div class="auth-card">
    <p v-if="eyebrow" class="auth-card__eyebrow">{{ eyebrow }}</p>
    <h1 v-if="title" class="auth-card__title">{{ title }}</h1>
    <p v-if="subtitle" class="auth-card__subtitle">{{ subtitle }}</p>
    <div class="auth-card__body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.auth-card {
  animation: auth-card-in 0.7s 0.1s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.auth-card__eyebrow {
  margin: 0 0 10px;
  color: var(--home-accent);
  font-size: 12px;
  letter-spacing: 0.24em;
}

.auth-card__title {
  margin: 0;
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: clamp(28px, 2.4vw, 34px);
  font-weight: 500;
  line-height: 1.3;
  letter-spacing: 0.04em;
}

.auth-card__subtitle {
  margin: 10px 0 0;
  color: var(--home-muted);
  font-size: 14px;
  line-height: 1.7;
}

.auth-card__body {
  margin-top: 32px;
}

@keyframes auth-card-in {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth-card {
    animation: none;
  }
}
</style>
