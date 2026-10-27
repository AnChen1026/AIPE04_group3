<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchAssignments } from '@/api/teacher'
import type { Assignment } from '@/types/api'
import { ASSIGNMENT_KIND_LABELS, dueText, toneClass } from '@/utils/format'

// 設計稿的「作業狀態」：老師發出的每一份作業，學生有沒有繳交。按「新增」到作業上傳，「查看詳情」看檔案與每次錄音的回饋
const route = useRoute()
const assignments = ref<Assignment[]>([])
const keyword = ref('')
const filter = ref<'all' | 'submitted' | 'missing'>('all')
const loaded = ref(false)
const error = ref('')

const filters = [
  { value: 'all', label: '全部' },
  { value: 'submitted', label: '已繳交' },
  { value: 'missing', label: '未繳交' },
] as const

// 網址帶 ?course= 時只看那門課（從課表的「查看作業分析」進來）
const onlyCourse = computed(() => (typeof route.query.course === 'string' ? route.query.course : ''))
const courseKeys = computed(() => [...new Set(assignments.value.map((item) => item.course_id))])
const shown = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return assignments.value.filter(
    (item) =>
      (!onlyCourse.value || item.course_id === onlyCourse.value) &&
      (filter.value === 'all' || (filter.value === 'submitted') === item.submission_count > 0) &&
      (!text || [item.student_name, item.course_title, item.title].some((value) => value.toLowerCase().includes(text))),
  )
})

function statusText(item: Assignment) {
  if (item.kind === 'quiz') return '題庫作業已發布'
  return item.submission_count ? `學生已繳交（${item.submission_count} 次）` : '作業已上傳，學生未繳交'
}

onMounted(async () => {
  try {
    assignments.value = await fetchAssignments()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到作業。'
  } finally {
    loaded.value = true
  }
})
</script>

<template>
  <PageHeader title="作業狀態">
    <label class="search-input">
      <span class="visually-hidden">搜尋學生</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋學生" />
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
    </label>
    <RouterLink :to="{ name: 'teacher-assignment-new', query: onlyCourse ? { course: onlyCourse } : {} }" class="btn btn--primary">
      新增
    </RouterLink>
  </PageHeader>

  <div class="chip-group homework__filters" role="group" aria-label="依繳交狀態篩選">
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
    <RouterLink v-if="onlyCourse" :to="{ name: 'teacher-practice' }" class="chip">看全部課程</RouterLink>
  </div>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="loaded && shown.length === 0" class="card empty">
    {{ assignments.length === 0 ? '還沒有發過作業。按右上角「新增」替已綁定的學生發第一份作業。' : '沒有符合的作業。' }}
  </div>
  <article v-for="item in shown" :key="item.id" class="tone-card homework" :class="toneClass(item.course_id, courseKeys)">
    <p class="tone-card__cell tone-card__title homework__type">{{ ASSIGNMENT_KIND_LABELS[item.kind] }}</p>
    <div class="tone-card__cell">
      <p class="tone-card__title">{{ item.course_title }}</p>
      <p class="tone-card__line">{{ item.student_name }}</p>
    </div>
    <div class="tone-card__cell">
      <p class="tone-card__title">{{ statusText(item) }}</p>
      <p class="tone-card__line">{{ item.title }}・{{ dueText(item.due_at) }}</p>
    </div>
    <RouterLink :to="{ name: 'teacher-assignment', params: { id: item.id } }" class="tone-btn">查看詳情</RouterLink>
  </article>
</template>

<style scoped>
.search-input {
  width: min(220px, 100%);
}

.homework__filters {
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 2px solid var(--home-line);
}

.homework {
  grid-template-columns: 130px minmax(0, 0.8fr) minmax(0, 1.6fr) auto;
}

.homework__type {
  text-align: center;
}

@media (max-width: 720px) {
  .homework__type {
    text-align: left;
  }
}
</style>
