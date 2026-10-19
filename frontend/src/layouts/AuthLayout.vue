<script setup lang="ts">
import photo from '@/assets/images/登入頁面圖片.png'
import '@/assets/styles/auth.css'

// 登入、註冊、忘記密碼、聯繫老師共用的版面：左邊照片、右邊表單。
// 在 App.vue 只掛一次，切換登入與註冊時照片不重新載入，只有右邊表單淡入淡出。
</script>

<template>
  <div class="auth-layout">
    <aside class="auth-layout__visual" aria-hidden="true">
      <img class="auth-layout__photo" :src="photo" alt="" />
      <div class="auth-layout__caption">
        <p class="auth-layout__mark">melo.</p>
        <p class="auth-layout__tagline">找一位老師，把想彈的曲子練完。</p>
      </div>
    </aside>

    <section class="auth-layout__panel">
      <header class="auth-layout__bar">
        <RouterLink to="/" class="auth-layout__brand" aria-label="melo 首頁">melo.</RouterLink>
        <RouterLink to="/" class="auth-layout__home">
          <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M10 3 5 8l5 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          回首頁
        </RouterLink>
      </header>

      <div class="auth-layout__body">
        <div class="auth-layout__form">
          <slot />
        </div>
      </div>

      <p class="auth-layout__footnote">© melo. 一對一鋼琴課</p>
    </section>
  </div>
</template>

<style scoped>
.auth-layout {
  display: grid;
  grid-template-columns: minmax(0, 55fr) minmax(0, 45fr);
  min-height: 100vh;
  background: var(--home-bg);
  color: var(--home-ink);
}

/* ---------- 左邊照片 */

.auth-layout__visual {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 16px 0 16px 16px;
}

.auth-layout__photo {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 24px;
  object-fit: cover;
  object-position: 60% 62%;
  animation: auth-photo-in 1.1s cubic-bezier(0.22, 1, 0.36, 1) both;
}

/* 很輕的暗色漸層，只為了讓上下的文字看得清楚 */
.auth-layout__visual::after {
  content: '';
  position: absolute;
  inset: 16px 0 16px 16px;
  border-radius: 24px;
  background:
    linear-gradient(0deg, rgba(46, 34, 24, 0.42) 0%, rgba(46, 34, 24, 0) 34%);
  pointer-events: none;
}

.auth-layout__caption {
  position: absolute;
  z-index: 1;
  left: clamp(40px, 4vw, 64px);
  margin: 0;
  color: #fffaf3;
  animation: auth-rise 0.9s 0.35s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.auth-layout__caption {
  bottom: clamp(44px, 5vw, 72px);
}

.auth-layout__caption p {
  margin: 0;
}

.auth-layout__mark {
  font-family: var(--font-logo);
  font-size: clamp(40px, 4.2vw, 60px);
  line-height: 1;
  letter-spacing: 0.01em;
}

.auth-layout__tagline {
  margin-top: 14px !important;
  font-family: var(--font-serif);
  font-size: clamp(15px, 1.25vw, 18px);
  letter-spacing: 0.12em;
  opacity: 0.94;
}

/* ---------- 右邊表單 */

.auth-layout__panel {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 28px clamp(24px, 5vw, 72px) 24px;
}

.auth-layout__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.auth-layout__brand {
  color: var(--home-ink);
  font-family: var(--font-logo);
  font-size: 26px;
  line-height: 1;
  letter-spacing: 0.01em;
}

.auth-layout__home {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 36px;
  padding: 0 12px;
  border-radius: var(--radius-pill);
  color: var(--home-muted);
  font-size: 13px;
  transition: background 0.2s ease, color 0.2s ease;
}

.auth-layout__home:hover {
  background: var(--home-cream);
  color: var(--home-ink);
}

.auth-layout__body {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  padding: clamp(32px, 6vh, 72px) 0;
}

.auth-layout__form {
  width: min(390px, 100%);
}

.auth-layout__footnote {
  margin: 0;
  color: #b3a597;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-align: center;
}

@keyframes auth-photo-in {
  from {
    opacity: 0;
    transform: scale(1.02);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes auth-rise {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ---------- 平板：照片窄一點 */
@media (max-width: 1023px) {
  .auth-layout {
    grid-template-columns: minmax(0, 44fr) minmax(0, 56fr);
  }
}

/* ---------- 手機：單欄，照片變成上方橫幅 */
@media (max-width: 768px) {
  .auth-layout {
    grid-template-columns: 1fr;
  }

  .auth-layout__visual {
    position: relative;
    height: 200px;
    padding: 12px 12px 0;
  }

  .auth-layout__visual::after {
    inset: 12px 12px 0;
    border-radius: 20px;
  }

  .auth-layout__photo {
    border-radius: 20px;
    object-position: 60% 66%;
  }

  .auth-layout__caption {
    bottom: 20px;
    left: 32px;
  }

  .auth-layout__mark {
    display: none;
  }

  .auth-layout__tagline {
    margin-top: 0 !important;
    font-size: 15px;
  }

  .auth-layout__panel {
    min-height: auto;
    padding: 20px 20px 28px;
  }

  .auth-layout__body {
    padding: 28px 0 32px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth-layout__photo,
  .auth-layout__caption {
    animation: none;
  }
}
</style>
