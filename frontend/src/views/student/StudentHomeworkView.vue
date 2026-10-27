<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchMyAssignments } from '@/api/student'
import type { Assignment } from '@/types/api'
import { ASSIGNMENT_KIND_LABELS, dueText, toneClass } from '@/utils/format'

// 設計稿的學生「作業狀態」：老師發給自己的每一份作業。演奏作業可以上傳錄音，題庫作業的作答尚未開放
const assignments = ref<Assignment[]>([])
const keyword = ref('')
const filter = ref<'all' | 'missing' | 'submitted'>('all')
const loaded = ref(false)
const error = ref('')

const filters = [
  { value: 'all', label: '全部' },
  { value: 'missing', label: '未繳交' },
  { value: 'submitted', label: '已繳交' },
] as const

const courseKeys = computed(() => [...new Set(assignments.value.map((item) => item.course_id))])
const shown = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return assignments.value.filter(
    (item) =>
      (filter.value === 'all' || (filter.value === 'submitted') === item.submission_count > 0) &&
      (!text || [item.course_title, item.title].some((value) => value.toLowerCase().includes(text))),
  )
})

function statusText(item: Assignment) {
  if (item.kind === 'quiz') return '題庫作業'
  return item.submission_count ? '作業已繳交' : '作業未繳交'
}

onMounted(async () => {
  try {
    assignments.value = await fetchMyAssignments()
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

  <div v-if="loaded && assignments.length === 0" class="card empty">
    老師還沒有發作業給你。老師發布後，會出現在這裡。
  </div>
  <div v-else-if="loaded && shown.length === 0" class="card empty">沒有符合的作業。</div>
  <article v-for="item in shown" :key="item.id" class="tone-card homework" :class="toneClass(item.course_id, courseKeys)">
    <p class="tone-card__cell tone-card__title homework__type">{{ ASSIGNMENT_KIND_LABELS[item.kind] }}</p>
    <div class="tone-card__cell">
      <p class="tone-card__title">{{ item.course_title }}</p>
      <p class="tone-card__line">{{ item.title }}</p>
    </div>
    <div class="tone-card__cell">
      <p class="tone-card__title">{{ statusText(item) }}</p>
      <p class="tone-card__line">{{ dueText(item.due_at) }}</p>
    </div>
    <div class="homework__actions">
      <RouterLink v-if="item.kind === 'performance'" :to="`/student/homework/${item.id}`" class="tone-btn">上傳</RouterLink>
      <button v-else type="button" class="tone-btn" disabled title="題庫作答尚未開放">作答</button>
      <RouterLink :to="{ path: `/student/homework/${item.id}`, hash: '#history' }" class="tone-btn">查看詳情</RouterLink>
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
