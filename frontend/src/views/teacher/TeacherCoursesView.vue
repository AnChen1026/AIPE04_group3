<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchMyCourses } from '@/api/teacher'
import type { Course } from '@/types/api'
import { apiUrl } from '@/api/http'
import { imageForCourse } from '@/assets/courseImages'
import { COURSE_STATUS_LABELS, deliveryText, priceText } from '@/utils/format'

const courses = ref<Course[]>([])
const keyword = ref('')
const status = ref<'all' | Course['status']>('all')
const error = ref('')

const filters: { value: 'all' | Course['status']; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'published', label: '已發布' },
  { value: 'draft', label: '草稿' },
  { value: 'archived', label: '已封存' },
]

const shown = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return courses.value.filter(
    (course) =>
      (status.value === 'all' || course.status === status.value) &&
      (!text || [course.title, course.style ?? '', course.region ?? ''].some((value) => value.toLowerCase().includes(text))),
  )
})

function statusClass(value: Course['status']) {
  return value === 'published' ? 'badge--accent' : value === 'draft' ? 'badge--warn' : 'badge--muted'
}

onMounted(async () => {
  try {
    courses.value = await fetchMyCourses()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到課程。'
  }
})
</script>

<template>
  <PageHeader title="課程管理" description="只有「已發布」的課會出現在首頁，學生也才能洽詢。">
    <label class="search-input">
      <span class="visually-hidden">搜尋課程</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋課程" />
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
    </label>
    <RouterLink to="/teacher/courses/new" class="btn btn--primary">新增課程</RouterLink>
  </PageHeader>

  <div class="chip-group courses__filters" role="group" aria-label="依狀態篩選">
    <button
      v-for="filter in filters"
      :key="filter.value"
      type="button"
      class="chip"
      :aria-pressed="status === filter.value"
      @click="status = filter.value"
    >
      {{ filter.label }}
    </button>
  </div>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="shown.length === 0" class="card empty">
    {{ courses.length === 0 ? '還沒有課程，先新增一門吧。' : '沒有符合的課程。' }}
  </div>
  <article v-for="course in shown" :key="course.id" class="card course">
    <img
      class="course__image"
      :src="course.image_url ? apiUrl(course.image_url) : imageForCourse(course.title, course.style)"
      :alt="course.title"
      loading="lazy"
    />
    <div class="course__body">
    <header class="course__head">
      <h2>{{ course.title }}</h2>
      <RouterLink :to="`/teacher/courses/${course.id}/edit`" class="btn btn--ghost btn--small">編輯</RouterLink>
    </header>
    <ul class="course__meta">
      <li>{{ course.style || '風格未填' }}</li>
      <li>{{ course.level || '程度未填' }}</li>
      <li>{{ deliveryText(course.delivery_mode) }}{{ course.region ? `・${course.region}` : '' }}</li>
      <li>{{ priceText(course.price_per_lesson) }}</li>
      <li v-if="course.time_slots">{{ course.time_slots }}</li>
    </ul>
    <footer class="course__foot">
      <span class="muted">{{ course.has_reference_midi ? '已設定參考 MIDI' : '尚未設定參考 MIDI，學生還不能送出練習錄音' }}</span>
      <span class="badge" :class="statusClass(course.status)">{{ COURSE_STATUS_LABELS[course.status] }}</span>
    </footer>
    </div>
  </article>
</template>

<style scoped>
.search-input {
  width: min(220px, 100%);
}

.courses__filters {
  margin-bottom: 16px;
}

.course {
  display: flex;
  gap: 20px;
}

.course__image {
  flex: none;
  width: 150px;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  border-radius: 16px;
  background: var(--home-cream);
}

.course__body {
  flex: 1;
  min-width: 0;
}

@media (max-width: 640px) {
  .course {
    flex-direction: column;
  }

  .course__image {
    width: 100%;
  }
}

.course__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.course__head h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.course__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  margin: 12px 0 0;
  padding: 0;
  color: var(--home-ink);
  font-size: 14px;
  list-style: none;
}

.course__meta li + li::before {
  content: '・';
  margin-right: 6px;
  color: var(--home-wood);
}

.course__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  font-size: 13px;
}
</style>
