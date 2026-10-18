<script setup lang="ts">
import { computed, ref } from 'vue'
import CourseCard from './CourseCard.vue'
import SectionHeading from './SectionHeading.vue'
import { courseLevels, type CourseCardData, type CourseLevel } from '@/mocks/home'

const props = defineProps<{
  courses: CourseCardData[]
}>()

const emit = defineEmits<{
  viewCourse: [title: string]
}>()

const level = ref<CourseLevel | null>(null)

const shownCourses = computed(() =>
  level.value ? props.courses.filter((course) => course.level === level.value) : props.courses,
)
</script>

<template>
  <section id="courses" class="courses" aria-labelledby="courses-title">
    <div class="courses__top">
      <SectionHeading
        v-reveal
        label="熱門課程"
        title="找一門"
        accent="剛好適合你的課"
        heading-id="courses-title"
      >
        依自己的程度挑選。不確定程度也沒關係，先和老師聊聊。
      </SectionHeading>

      <div v-reveal="120" class="courses__levels" role="group" aria-label="依程度篩選">
        <button type="button" :aria-pressed="level === null" @click="level = null">全部</button>
        <button
          v-for="item in courseLevels"
          :key="item"
          type="button"
          :aria-pressed="level === item"
          @click="level = item"
        >
          {{ item }}
        </button>
      </div>
    </div>

    <p v-if="shownCourses.length === 0" class="courses__empty">目前沒有符合的課程，換個條件看看。</p>
    <div v-else class="courses__grid">
      <CourseCard
        v-for="(course, index) in shownCourses"
        :key="course.id"
        v-reveal="index * 90"
        :course="course"
        @view-course="emit('viewCourse', $event)"
      />
    </div>
  </section>
</template>

<style scoped>
.courses {
  width: min(1160px, calc(100% - 48px));
  margin: 0 auto;
  padding: var(--section-space) 0;
}

.courses__top {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.courses__levels {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.courses__levels button {
  padding: 8px 18px;
  border: 1px solid var(--home-wood);
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--home-ink);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.courses__levels button:hover {
  border-color: var(--home-accent);
}

.courses__levels button[aria-pressed='true'] {
  border-color: var(--home-accent);
  background: var(--home-accent);
  color: var(--home-paper);
}

.courses__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 32px 28px;
  margin-top: 48px;
}

.courses__empty {
  margin-top: 40px;
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
}
</style>
