<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchMyAssignments } from '@/api/student'
import type { Assignment } from '@/types/api'
import { KIND_INFO, type AnalysisKind } from '@/composables/useAssignmentAttempts'
import { toneClass } from '@/utils/format'

// 設計稿「作業分析-演奏作業／題庫作業」：依課程篩選，每份作業一張卡片（作業內容、練習次數、老師），按「查看詳情」看每次練習
const route = useRoute()
const kind = computed(() => (route.params.kind === 'quiz' ? 'quiz' : 'performance') as AnalysisKind)
const info = computed(() => KIND_INFO[kind.value])
const assignments = ref<Assignment[]>([])
const course = ref('')
const loaded = ref(false)
const error = ref('')

const ofKind = computed(() => assignments.value.filter((item) => item.kind === kind.value))
const courses = computed(() => [...new Map(ofKind.value.map((item) => [item.course_id, item.course_title])).entries()])
const courseKeys = computed(() => courses.value.map(([id]) => id))
const shown = computed(() => ofKind.value.filter((item) => !course.value || item.course_id === course.value))

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
  <PageHeader title="作業分析">
    <RouterLink :to="{ name: 'student-analysis-list', params: { kind: info.other } }" class="analysis__switch">
      查看{{ KIND_INFO[info.other].label }}分析
    </RouterLink>
    <RouterLink :to="{ name: 'student-analysis' }" class="btn btn--primary">返回</RouterLink>
  </PageHeader>

  <h2 class="analysis__kind" :class="`analysis__kind--${kind}`">
    <span aria-hidden="true">{{ info.icon }}</span> {{ info.label }} <small>{{ info.hint }}</small>
  </h2>

  <div v-if="courses.length > 1" class="chip-group analysis__courses" role="group" aria-label="依課程篩選">
    <button type="button" class="chip" :aria-pressed="course === ''" @click="course = ''">全部</button>
    <button v-for="[id, title] in courses" :key="id" type="button" class="chip" :aria-pressed="course === id" @click="course = id">
      {{ title }}
    </button>
  </div>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="loaded && shown.length === 0" class="card empty">還沒有{{ info.label }}。</div>
  <article v-for="item in shown" :key="item.id" class="tone-card analysis" :class="kind === 'quiz' ? 'tone-card--1' : toneClass(item.course_id, courseKeys)">
    <p class="tone-card__cell tone-card__title analysis__course">{{ item.course_title }}</p>
    <div class="tone-card__cell">
      <p class="tone-card__title">作業內容：{{ item.title }}</p>
      <p class="tone-card__line">練習次數：{{ item.submission_count }} 次</p>
    </div>
    <p class="tone-card__cell tone-card__title">{{ item.teacher_name }}老師</p>
    <RouterLink :to="{ name: 'student-analysis-attempts', params: { kind, id: item.id } }" class="tone-btn">查看詳情</RouterLink>
  </article>
</template>

<style scoped>
.analysis__switch {
  align-self: center;
  color: var(--home-muted);
}

.analysis__switch:hover {
  color: var(--home-accent);
}

.analysis__kind {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 0 0 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--home-line);
  font-size: 22px;
  font-weight: 500;
}

.analysis__kind small {
  color: var(--home-muted);
  font-size: 15px;
}

.analysis__kind--performance {
  color: #3f8f2a;
}

.analysis__kind--quiz {
  color: #1f66b8;
}

.analysis__courses {
  margin-bottom: 18px;
}

.analysis {
  grid-template-columns: 130px minmax(0, 1.6fr) minmax(0, 0.8fr) auto;
}

.analysis__course {
  text-align: center;
}

@media (max-width: 720px) {
  .analysis__course {
    text-align: left;
  }
}
</style>
