<script setup lang="ts">
import TeacherCard from './TeacherCard.vue'
import type { TeacherCardData } from '@/mocks/home'

defineProps<{
  teachers: TeacherCardData[]
}>()

const emit = defineEmits<{
  viewCourses: [teacherName: string]
}>()
</script>

<template>
  <section id="teachers" class="teachers" aria-labelledby="teachers-title">
    <div class="teachers__heading">
      <p>Featured Teachers</p>
      <h2 id="teachers-title">認識老師</h2>
    </div>

    <p v-if="teachers.length === 0" class="teachers__empty">找不到符合的老師。</p>
    <div v-else class="teachers__grid">
      <TeacherCard
        v-for="teacher in teachers"
        :key="teacher.id"
        :teacher="teacher"
        @view-courses="emit('viewCourses', $event)"
      />
    </div>
  </section>
</template>

<style scoped>
.teachers {
  width: min(1120px, calc(100% - 48px));
  margin: var(--section-space) auto 0;
}

.teachers__heading p {
  margin: 0;
  color: var(--home-accent);
  font-size: 13px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.teachers__heading h2 {
  margin: 6px 0 0;
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: 36px;
  font-weight: 600;
}

.teachers__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 22px;
  margin-top: 28px;
}

.teachers__empty {
  margin-top: 24px;
  color: var(--home-muted);
}

@media (max-width: 980px) {
  .teachers__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .teachers {
    width: calc(100% - 32px);
  }

  .teachers__grid {
    grid-template-columns: 1fr;
  }

  .teachers__heading h2 {
    font-size: 30px;
  }
}
</style>
