<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchPublishedCourses } from '@/api/courses'
import CourseCarousel from '@/components/course/CourseCarousel.vue'
import type { CourseSummary } from '@/types/course'

const STYLE_ORDER = ['流行鋼琴', '古典鋼琴', '爵士鋼琴']

const POPULAR_COUNT = 18

const courses = ref<CourseSummary[]>([])
const popularCourses = ref<CourseSummary[]>([])
const loading = ref(true)
const errorMessage = ref('')

function shuffleCourses(items: CourseSummary[]) {
  const copy = [...items]
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1))
    const current = copy[index]
    copy[index] = copy[swapIndex]
    copy[swapIndex] = current
  }
  return copy
}

const rows = computed(() => {
  const groups = new Map<string, CourseSummary[]>()
  for (const course of courses.value) {
    const name = course.style || '其他課程'
    const list = groups.get(name) ?? []
    list.push(course)
    groups.set(name, list)
  }
  const names = [
    ...STYLE_ORDER.filter((name) => groups.has(name)),
    ...[...groups.keys()].filter((name) => !STYLE_ORDER.includes(name)),
  ]
  return names.map((title) => ({ title, courses: groups.get(title) ?? [] }))
})

async function loadCourses() {
  loading.value = true
  errorMessage.value = ''
  try {
    courses.value = await fetchPublishedCourses()
    popularCourses.value = shuffleCourses(courses.value).slice(0, POPULAR_COUNT)
  } catch {
    errorMessage.value = '課程載入失敗，請稍後再試。'
  } finally {
    loading.value = false
  }
}

onMounted(loadCourses)
</script>

<template>
  <div class="home">
    <p v-if="loading" class="home__status">課程載入中…</p>

    <div v-else-if="errorMessage" class="home__status">
      <p>{{ errorMessage }}</p>
      <button type="button" class="home__retry" @click="loadCourses">重新載入</button>
    </div>

    <p v-else-if="rows.length === 0" class="home__status">目前還沒有已發布的課程。</p>

    <template v-else>
      <CourseCarousel
        v-if="popularCourses.length"
        title="熱門課程"
        :courses="popularCourses"
      />
      <CourseCarousel
        v-for="row in rows"
        :key="row.title"
        :title="row.title"
        :courses="row.courses"
      />
    </template>
  </div>
</template>

<style scoped>
.home {
  min-height: calc(100vh - var(--header-height));
  padding: 8px 0 96px;
  background: #fbf6ef;
  color: #1c1c1c;
}

.home :deep(.row) {
  margin-top: 64px;
}

.home :deep(.row:first-of-type) {
  margin-top: 20px;
}

.home__status {
  padding: 48px 16px;
  text-align: center;
  color: #555555;
}

.home__retry {
  margin-top: 12px;
  padding: 8px 20px;
  border: 1px solid #1c1c1c;
  border-radius: var(--radius-pill);
  background: transparent;
  color: #1c1c1c;
  cursor: pointer;
}
</style>
