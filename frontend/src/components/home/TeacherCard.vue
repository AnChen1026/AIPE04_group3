<script setup lang="ts">
import type { TeacherCardData } from '@/mocks/home'

defineProps<{
  teacher: TeacherCardData
}>()

const emit = defineEmits<{
  viewCourses: [teacherName: string]
}>()
</script>

<template>
  <article class="teacher-card">
    <img :src="teacher.photo" :alt="`${teacher.name}的照片`" />
    <div class="teacher-card__body">
      <p class="teacher-card__specialty">{{ teacher.specialty }}</p>
      <h3>{{ teacher.name }}</h3>
      <p class="teacher-card__bio">{{ teacher.bio }}</p>
      <button type="button" @click="emit('viewCourses', teacher.name)">看這位老師的課</button>
    </div>
  </article>
</template>

<style scoped>
.teacher-card {
  overflow: hidden;
  border-radius: var(--radius-card);
  background: var(--home-paper);
  box-shadow: var(--shadow-soft);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.teacher-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 36px rgba(80, 58, 40, 0.12);
}

.teacher-card img {
  width: 100%;
  aspect-ratio: 4 / 5;
  object-fit: cover;
  object-position: center 18%;
}

.teacher-card__body {
  padding: 16px 16px 18px;
}

.teacher-card__specialty {
  margin: 0;
  color: var(--home-accent);
  font-size: 13px;
  letter-spacing: 0.04em;
}

.teacher-card h3 {
  margin: 6px 0 0;
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 600;
}

.teacher-card__bio {
  min-height: 3em;
  margin: 8px 0 0;
  color: var(--home-muted);
  font-size: 14px;
}

.teacher-card button {
  margin-top: 14px;
  padding: 8px 14px;
  border: 1px solid var(--home-wood);
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--home-ink);
  cursor: pointer;
}

.teacher-card button:hover {
  background: var(--home-wood);
}

@media (prefers-reduced-motion: reduce) {
  .teacher-card {
    transition: none;
  }

  .teacher-card:hover {
    transform: none;
  }
}
</style>
