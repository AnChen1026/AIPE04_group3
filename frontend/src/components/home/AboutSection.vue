<script setup lang="ts">
import SectionHeading from './SectionHeading.vue'
import ArrowButton from './ArrowButton.vue'
import type { HighlightItem } from '@/mocks/home'

defineProps<{
  photos: { src: string; alt: string }[]
  highlights: HighlightItem[]
}>()
</script>

<template>
  <section id="about" class="about" aria-labelledby="about-title">
    <div class="about__intro">
      <SectionHeading
        v-reveal
        label="關於melo"
        title="想開始上課"
        accent="從找到對的老師開始"
        heading-id="about-title"
        align="center"
      >
        不論是第一次彈琴，還是想重新找回以前的樂感，都能在這裡找到步調相近的老師
      </SectionHeading>

      <div class="about__photos" aria-hidden="true">
        <img
          v-for="(photo, index) in photos"
          :key="photo.src"
          v-reveal="index * 120"
          :src="photo.src"
          :alt="photo.alt"
          loading="lazy"
        />
      </div>
    </div>

    <ol class="about__list">
      <li v-for="(item, index) in highlights" :key="item.title" v-reveal="index * 100">
        <span class="about__index">{{ String(index + 1).padStart(2, '0') }}</span>
        <h3>{{ item.title }}</h3>
        <p>{{ item.text }}</p>
      </li>
    </ol>

    <div v-reveal class="about__action">
      <ArrowButton href="#flow">看看怎麼開始</ArrowButton>
    </div>
  </section>
</template>

<style scoped>
.about {
  width: min(1160px, calc(100% - 48px));
  margin: 0 auto;
  padding: var(--section-space) 0 0;
}

.about__photos {
  display: flex;
  justify-content: center;
  margin-top: 48px;
}

/* 三張照片微微錯開、旋轉，像放在琴譜架上的明信片 */
.about__photos img {
  width: clamp(120px, 18vw, 200px);
  aspect-ratio: 4 / 5;
  object-fit: cover;
  border: 6px solid var(--home-paper);
  border-radius: 22px;
  box-shadow: var(--shadow-soft);
}

.about__photos img:nth-child(1) {
  rotate: -7deg;
  margin-right: -18px;
  margin-top: 18px;
}

.about__photos img:nth-child(2) {
  z-index: 1;
}

.about__photos img:nth-child(3) {
  rotate: 7deg;
  margin-left: -18px;
  margin-top: 18px;
}

.about__list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 64px 0 0;
  padding: 0;
  border: 1px solid var(--home-line);
  border-radius: var(--radius-card);
  background: var(--home-paper);
  list-style: none;
}

.about__list li {
  padding: 32px 28px;
  text-align: center;
}

.about__list li + li {
  border-left: 1px solid var(--home-line);
}

.about__index {
  color: var(--home-accent);
  font-family: var(--font-serif);
  font-size: 30px;
}

.about__list h3 {
  margin: 8px 0 0;
  color: var(--home-ink);
  font-size: 19px;
  font-weight: 500;
}

.about__list p {
  margin: 10px 0 0;
  color: var(--home-muted);
  font-size: 14px;
  line-height: 1.8;
}

.about__action {
  display: flex;
  justify-content: center;
  margin-top: 36px;
}

@media (max-width: 860px) {
  .about__list {
    grid-template-columns: 1fr;
  }

  .about__list li + li {
    border-top: 1px solid var(--home-line);
    border-left: 0;
  }
}

@media (max-width: 640px) {
  .about {
    width: calc(100% - 32px);
  }

  .about__list li {
    padding: 26px 20px;
  }
}
</style>
