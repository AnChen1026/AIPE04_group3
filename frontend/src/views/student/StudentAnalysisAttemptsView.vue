<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import { KIND_INFO, useAssignmentAttempts, type AnalysisKind } from '@/composables/useAssignmentAttempts'
import { dateOnly } from '@/utils/format'

// 設計稿「作業分析-演奏作業列表／題庫作業列表」：這份作業的第幾次練習、上傳日期，「詳細分析」看這次、「練習對比」跟上一次比
const route = useRoute()
const kind = computed(() => (route.params.kind === 'quiz' ? 'quiz' : 'performance') as AnalysisKind)
const info = computed(() => KIND_INFO[kind.value])
const assignmentId = String(route.params.id)
const { assignment, attempts, error, loaded, load, heading } = useAssignmentAttempts(assignmentId)

const ORDINALS = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
function ordinal(no: number) {
  return no <= 10 ? ORDINALS[no - 1] : String(no)
}

onMounted(load)
</script>

<template>
  <PageHeader :title="info.label">
    <RouterLink :to="{ name: 'student-analysis-list', params: { kind: info.other } }" class="analysis__switch">
      查看{{ KIND_INFO[info.other].label }}分析
    </RouterLink>
    <RouterLink :to="{ name: 'student-analysis-list', params: { kind } }" class="btn btn--primary">返回</RouterLink>
  </PageHeader>

  <h2 class="analysis__heading" :class="`analysis__heading--${kind}`">{{ heading }}</h2>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="loaded && assignment && attempts.length === 0" class="card empty">還沒有練習紀錄。</div>
  <article v-for="item in attempts" :key="item.no" class="tone-card attempt" :class="kind === 'quiz' ? 'tone-card--1' : ''">
    <p class="tone-card__cell tone-card__title">第{{ ordinal(item.no) }}次練習</p>
    <p class="tone-card__cell tone-card__line">作業上傳日期：{{ dateOnly(item.submittedAt) }}</p>
    <div class="tone-card__cell attempt__actions">
      <RouterLink :to="{ name: 'student-analysis-detail', params: { kind, id: assignmentId, attempt: item.no } }" class="tone-btn">詳細分析</RouterLink>
      <RouterLink
        v-if="item.no > 1"
        :to="{ name: 'student-analysis-compare', params: { kind, id: assignmentId, attempt: item.no } }"
        class="tone-btn"
      >
        練習對比
      </RouterLink>
      <span v-else class="tone-btn attempt__disabled" title="第一次練習沒有可以比較的上一次">練習對比</span>
    </div>
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

.analysis__heading {
  margin: 0 0 18px;
  font-size: 24px;
}

.analysis__heading--performance {
  color: #c08a52;
}

.analysis__heading--quiz {
  color: #1f66b8;
}

.attempt {
  grid-template-columns: 140px minmax(0, 1fr) auto;
}

.attempt__actions {
  display: flex;
  gap: 12px;
}

.attempt__disabled {
  cursor: not-allowed;
  opacity: 0.45;
}
</style>
