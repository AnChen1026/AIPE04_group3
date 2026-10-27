<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchMyRecordings } from '@/api/student'
import { useBoundCourses } from '@/composables/useBoundCourses'
import type { Recording } from '@/types/api'
import { RECORDING_STATUS_LABELS, formatDateTime, toneClass } from '@/utils/format'

// 設計稿的學生「作業狀態」：每門已綁定的課一張演奏作業卡（照老師的參考曲錄音），可以上傳或看詳情。
// 題庫作業與繳交期限後端還沒有，先留位置
const courses = useBoundCourses()
const recordings = ref<Record<string, Recording[]>>({})
const keyword = ref('')
const filter = ref<'all' | 'missing' | 'submitted'>('all')
const error = ref('')

const filters = [
  { value: 'all', label: '全部' },
  { value: 'missing', label: '未繳交' },
  { value: 'submitted', label: '已繳交' },
] as const

const courseKeys = computed(() => courses.bound.value.map((item) => item.course_id))
const shown = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return courses.bound.value.filter((item) => {
    const submitted = (recordings.value[item.course_id] ?? []).length > 0
    return (
      (filter.value === 'all' || (filter.value === 'submitted') === submitted) &&
      (!text || [item.course_title ?? '', item.teacher_name ?? ''].some((value) => value.toLowerCase().includes(text)))
    )
  })
})

function latest(courseId: string) {
  return recordings.value[courseId]?.[0] ?? null
}

onMounted(async () => {
  try {
    await courses.load()
    const lists = await Promise.all(courses.bound.value.map((item) => fetchMyRecordings(item.course_id)))
    recordings.value = Object.fromEntries(courses.bound.value.map((item, index) => [item.course_id, lists[index]!]))
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到作業。'
  }
})
</script>

<template>
  <PageHeader title="作業狀態">
    <label class="search-input">
      <span class="visually-hidden">搜尋課程</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋課程" />
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
    </label>
  </PageHeader>

  <div class="homework__bar">
    <div class="chip-group" role="group" aria-label="依繳交狀態篩選">
      <button
        v-for="item in filters"
        :key="item.value"
        type="button"
        class="chip"
        :aria-pressed="filter === item.value"
        @click="filter = item.value"
      >
        {{ item.label }}
      </button>
    </div>
    <RouterLink to="/student/homework/analysis" class="homework__analysis">查看作業分析</RouterLink>
  </div>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="courses.loaded.value && courses.bound.value.length === 0" class="card empty">
    還沒有進入任何課程。在「老師」頁輸入老師給的綁定碼後，就能在這裡交作業。
  </div>
  <div v-else-if="courses.loaded.value && shown.length === 0" class="card empty">沒有符合的作業。</div>
  <article
    v-for="item in shown"
    :key="item.course_id"
    class="tone-card homework"
    :class="toneClass(item.course_id, courseKeys)"
  >
    <p class="tone-card__cell tone-card__title homework__type">演奏作業</p>
    <div class="tone-card__cell">
      <p class="tone-card__title">{{ item.course_title }}</p>
      <p class="tone-card__line">{{ item.teacher_name }}老師</p>
    </div>
    <div class="tone-card__cell">
      <p class="tone-card__title">{{ latest(item.course_id) ? '作業已繳交' : '作業未繳交' }}</p>
      <p class="tone-card__line">
        <template v-if="latest(item.course_id)">
          最近繳交：{{ formatDateTime(latest(item.course_id)!.submitted_at) }}（{{ RECORDING_STATUS_LABELS[latest(item.course_id)!.status] }}）
        </template>
        <template v-else>繳交期限：未設定</template>
      </p>
    </div>
    <div class="homework__actions">
      <RouterLink :to="{ path: '/student/homework/practice', query: { course: item.course_id } }" class="tone-btn">上傳</RouterLink>
      <RouterLink :to="{ path: '/student/homework/practice', query: { course: item.course_id }, hash: '#history' }" class="tone-btn">
        查看詳情
      </RouterLink>
    </div>
  </article>
</template>

<style scoped>
.search-input {
  width: min(220px, 100%);
}

.homework__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 2px solid var(--home-line);
}

.homework__analysis {
  color: var(--home-muted);
}

.homework__analysis:hover {
  color: var(--home-accent);
}

.homework {
  grid-template-columns: 130px minmax(0, 0.8fr) minmax(0, 1.6fr) auto;
}

.homework__type {
  text-align: center;
}

.homework__actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

@media (max-width: 720px) {
  .homework__type {
    text-align: left;
  }

  .homework__actions {
    flex-direction: row;
  }
}
</style>
