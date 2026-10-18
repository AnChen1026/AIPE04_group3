<script setup lang="ts">
import { computed } from 'vue'
import type { CourseCardData } from '@/mocks/home'

const props = defineProps<{
  course: CourseCardData
}>()

const emit = defineEmits<{
  viewCourse: [title: string]
}>()

const coverPosition = computed(() => {
  if (props.course.category.includes('流行')) return 'center 100%'
  return 'center 68%'
})

const price = computed(() => `NT$ ${props.course.price.toLocaleString('zh-TW')}`)
</script>

<template>
  <article class="course-card">
    <div class="course-card__cover">
      <img :src="course.cover" :alt="course.title" :style="{ objectPosition: coverPosition }" loading="lazy" />
      <span class="course-card__chip course-card__chip--level">{{ course.level }}</span>
      <span class="course-card__chip course-card__chip--time">{{ course.minutes }} 分鐘</span>
    </div>
    <div class="course-card__body">
      <p class="course-card__category">{{ course.category }}・{{ course.format }}</p>
      <h3>{{ course.title }}</h3>
      <p class="course-card__summary">{{ course.summary }}</p>
      <div class="course-card__footer">
        <p>
          <span>{{ course.teacherName }}</span>
          <strong>{{ price }}<small> / 堂</small></strong>
        </p>
        <button type="button" @click="emit('viewCourse', course.title)">
          看課程
          <span aria-hidden="true">→</span>
        </button>
      </div>
    </div>
  </article>
</template>

<style scoped>
.course-card {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.course-card__cover {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-card);
}

.course-card img {
  width: 100%;
  aspect-ratio: 4 / 3.4;
  object-fit: cover;
  transition: transform 0.8s cubic-bezier(0.22, 1, 0.36, 1);
}

.course-card:hover img {
  transform: scale(1.04);
}

.course-card__chip {
  position: absolute;
  bottom: 14px;
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  background: rgba(255, 250, 243, 0.94);
  color: var(--home-ink);
  font-size: 13px;
}

.course-card__chip--level {
  left: 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.course-card__chip--level::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--home-accent);
}

.course-card__chip--time {
  right: 14px;
}

.course-card__body {
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 20px 4px 0;
}

.course-card__category {
  margin: 0;
  color: var(--home-accent);
  font-size: 13px;
  letter-spacing: 0.06em;
}

.course-card h3 {
  margin: 6px 0 0;
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: 23px;
  font-weight: 600;
}

.course-card__summary {
  flex: 1;
  margin: 10px 0 0;
  color: var(--home-muted);
  font-size: 14px;
  line-height: 1.75;
}

.course-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px dashed var(--home-wood);
}

.course-card__footer p {
  display: flex;
  flex-direction: column;
  margin: 0;
  color: var(--home-muted);
  font-size: 13px;
}

.course-card__footer strong {
  color: var(--home-ink);
  font-size: 16px;
  font-weight: 500;
}

.course-card__footer small {
  color: var(--home-muted);
  font-size: 12px;
}

.course-card button {
  display: inline-flex;
  gap: 6px;
  padding: 9px 18px;
  border: 0;
  border-radius: var(--radius-pill);
  background: var(--home-accent);
  color: var(--home-paper);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.course-card button:hover {
  background: var(--home-accent-dark);
}

@media (prefers-reduced-motion: reduce) {
  .course-card img {
    transition: none;
  }

  .course-card:hover img {
    transform: none;
  }
}
</style>
