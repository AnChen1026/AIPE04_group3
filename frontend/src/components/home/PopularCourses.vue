<script setup lang="ts">
import CourseCard from './CourseCard.vue'
import type { CourseCardData } from '@/mocks/home'

defineProps<{
  courses: CourseCardData[]
}>()

const emit = defineEmits<{
  viewCourse: [title: string]
}>()
</script>

<template>
  <section id="courses" class="courses" aria-labelledby="courses-title">
    <div class="courses__heading">
      <p>Popular Courses</p>
      <h2 id="courses-title">熱門課程</h2>
    </div>

    <p v-if="courses.length === 0" class="courses__empty">找不到符合的課程。</p>
    <div v-else class="courses__grid">
      <CourseCard
        v-for="course in courses"
        :key="course.id"
        :course="course"
        @view-course="emit('viewCourse', $event)"
      />
    </div>
  </section>
</template>

<style scoped>
.courses {
  width: min(1120px, calc(100% - 48px));
  margin: var(--section-space) auto 0;
}

.courses__heading p {
  margin: 0;
  color: var(--home-accent);
  font-size: 13px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.courses__heading h2 {
  margin: 6px 0 0;
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: 36px;
  font-weight: 600;
}

.courses__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
  margin-top: 28px;
}

.courses__empty {
  margin-top: 24px;
  color: var(--home-muted);
}

@media (max-width: 980px) {
  .courses__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .courses {
    width: calc(100% - 32px);
  }

  .courses__grid {
    grid-template-columns: 1fr;
  }

  .courses__heading h2 {
    font-size: 30px;
  }
}
</style>
