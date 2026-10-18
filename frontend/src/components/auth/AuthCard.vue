<script setup lang="ts">
import coverImage from '@/assets/images/封面大圖.png'

// 登入、註冊、忘記密碼共用的外框：左邊一張暖色大圖，右邊是表單卡片
defineProps<{ title?: string; subtitle?: string }>()
</script>

<template>
  <div class="auth">
    <aside class="auth__visual" aria-hidden="true">
      <img :src="coverImage" alt="" />
      <div class="auth__quote">
        <p>找一位老師，</p>
        <p class="auth__quote-accent">把想彈的曲子練完。</p>
      </div>
    </aside>
    <section class="auth__panel">
      <div class="auth__card">
        <RouterLink to="/" class="auth__brand">琴室</RouterLink>
        <p class="auth__platform">鋼琴課程管理與推廣平台</p>
        <h1 v-if="title" class="auth__title">{{ title }}</h1>
        <p v-if="subtitle" class="auth__subtitle">{{ subtitle }}</p>
        <slot />
      </div>
    </section>
  </div>
</template>

<style scoped>
.auth {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  min-height: 100vh;
  background: var(--home-cream);
}

.auth__visual {
  position: relative;
  overflow: hidden;
}

.auth__visual img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 62%;
  filter: saturate(0.82) sepia(0.12);
}

.auth__visual::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(62, 52, 44, 0) 40%, rgba(52, 42, 34, 0.55));
}

.auth__quote {
  position: absolute;
  z-index: 1;
  right: 48px;
  bottom: 48px;
  left: 48px;
  color: var(--home-paper);
  font-size: clamp(26px, 2.6vw, 38px);
  font-weight: 500;
  line-height: 1.3;
}

.auth__quote p {
  margin: 0;
}

.auth__quote-accent {
  font-family: var(--font-serif);
  color: #f6e7d2;
}

.auth__panel {
  display: grid;
  place-items: center;
  padding: clamp(20px, 5vw, 64px) 16px;
}

.auth__card {
  width: min(460px, 100%);
  padding: clamp(28px, 4vw, 44px);
  border-radius: 32px;
  background: var(--home-paper);
  box-shadow: var(--shadow-soft);
}

.auth__brand {
  display: block;
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: 30px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-align: center;
}

.auth__platform {
  margin: 2px 0 0;
  color: var(--home-muted);
  font-size: 13px;
  letter-spacing: 0.08em;
  text-align: center;
}

.auth__title {
  margin: 22px 0 0;
  color: var(--home-accent);
  font-size: 22px;
  font-weight: 500;
  text-align: center;
}

.auth__subtitle {
  margin: 8px 0 0;
  color: var(--home-muted);
  font-size: 14px;
  text-align: center;
}

@media (max-width: 900px) {
  .auth {
    grid-template-columns: 1fr;
  }

  .auth__visual {
    display: none;
  }
}
</style>
