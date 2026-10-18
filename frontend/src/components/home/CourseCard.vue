<script setup lang="ts">
import { computed } from 'vue'
import type { CourseCardData } from '@/mocks/home'

const props = defineProps<{
  course: CourseCardData
}>()

const coverPosition = computed(() => {
  if (props.course.category.includes('流行')) return 'center 100%'
  return 'center 68%'
})

const emit = defineEmits<{
  viewCourse: [title: string]
}>()
</script>

<template>
  <article class="course-card">
    <div class="course-card__cover">
      <img :src="course.cover" :alt="course.title" :style="{ objectPosition: coverPosition }" />
      <span>{{ course.category }}</span>
    </div>
    <div class="course-card__body">
      <h3>{{ course.title }}</h3>
      <p>{{ course.teacherName }}</p>
      <button type="button" @click="emit('viewCourse', course.title)">查看這門課</button>
    </div>
  </article>
</template>

<style scoped>
.course-card {
  overflow: hidden;
  border-radius: var(--radius-card);
  background: var(--home-paper);
  box-shadow: var(--shadow-soft);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 36px rgba(80, 58, 40, 0.12);
}

.course-card__cover {
  position: relative;
}

.course-card img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
}

.course-card__cover span {
  position: absolute;
  top: 14px;
  left: 14px;
  padding: 6px 10px;
  border-radius: var(--radius-pill);
  background: rgba(255, 250, 243, 0.92);
  color: var(--home-ink);
  font-size: 13px;
}

.course-card__body {
  padding: 16px 16px 18px;
}

.course-card h3 {
  margin: 0;
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 600;
}

.course-card p {
  margin: 6px 0 0;
  color: var(--home-muted);
}

.course-card button {
  margin-top: 16px;
  padding: 8px 14px;
  border: 0;
  border-radius: var(--radius-pill);
  background: var(--home-accent);
  color: var(--home-paper);
  cursor: pointer;
}

.course-card button:hover {
  background: var(--home-accent-dark);
}

@media (prefers-reduced-motion: reduce) {
  .course-card {
    transition: none;
  }

  .course-card:hover {
    transform: none;
  }
}
</style>
