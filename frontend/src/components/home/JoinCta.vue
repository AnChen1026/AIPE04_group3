<script setup lang="ts">
import ArrowButton from './ArrowButton.vue'
import coverImage from '@/assets/images/封面大圖.png'
</script>

<template>
  <section class="join" aria-labelledby="join-title">
    <div v-reveal class="join__card">
      <img :src="coverImage" alt="" aria-hidden="true" loading="lazy" />
      <div class="join__copy">
        <h2 id="join-title">今天就找一首<em>想彈的曲子</em>開始</h2>
        <p>學生免費註冊；鋼琴老師可以申請開課，經平台審核後就能發布課程。</p>
        <div class="join__actions">
          <ArrowButton to="/signup" variant="light">我要找課</ArrowButton>
          <RouterLink to="/signup" class="join__link">我是老師，想開課 →</RouterLink>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.join {
  width: min(1160px, calc(100% - 48px));
  margin: 0 auto;
}

.join__card {
  position: relative;
  overflow: hidden;
  border-radius: 32px;
  color: var(--home-paper);
}

.join__card img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 70%;
  filter: saturate(0.8) sepia(0.15);
}

.join__card::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(90deg, rgba(62, 48, 38, 0.78), rgba(62, 48, 38, 0.25));
}

.join__copy {
  position: relative;
  z-index: 2;
  max-width: 560px;
  padding: clamp(40px, 7vw, 80px);
}

.join h2 {
  margin: 0;
  font-size: clamp(28px, 3.4vw, 42px);
  font-weight: 500;
  line-height: 1.35;
}

.join h2 em {
  font-family: var(--font-serif);
  font-style: normal;
  color: #f6e7d2;
}

.join p {
  margin: 16px 0 0;
  color: rgba(255, 250, 243, 0.85);
  line-height: 1.8;
}

.join__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 20px;
  margin-top: 28px;
}

.join__link {
  border-bottom: 1px solid rgba(255, 250, 243, 0.5);
  font-size: 15px;
}

.join__link:hover {
  border-color: var(--home-paper);
}

@media (max-width: 640px) {
  .join {
    width: calc(100% - 32px);
  }
}
</style>
