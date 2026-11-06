<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchMyAssignments } from '@/api/student'
import { KIND_INFO, type AnalysisKind } from '@/composables/useAssignmentAttempts'

// 設計稿「學生-作業」：點「作業」先選類型，左邊演奏作業、右邊題庫作業。
// 選了之後每份作業的繳交狀態和每次練習的分析在同一頁（StudentHomeworkKindView）
const KINDS: AnalysisKind[] = ['performance', 'quiz']
// 還沒繳交的份數，卡片上提醒一下
const missing = ref<Record<AnalysisKind, number>>({ performance: 0, quiz: 0 })

onMounted(async () => {
  const list = await fetchMyAssignments().catch(() => [])
  for (const kind of KINDS) missing.value[kind] = list.filter((item) => item.kind === kind && item.submission_count === 0).length
})
</script>

<template>
  <PageHeader title="作業" />

  <div class="kinds">
    <RouterLink
      v-for="kind in KINDS"
      :key="kind"
      :to="{ name: 'student-homework-kind', params: { kind } }"
      class="kind"
      :class="`kind--${kind}`"
    >
      <span class="kind__icon" aria-hidden="true">{{ KIND_INFO[kind].icon }}</span>
      <strong>{{ KIND_INFO[kind].label }}</strong>
      <span class="kind__hint">{{ KIND_INFO[kind].hint }}</span>
      <span v-if="missing[kind]" class="kind__badge">{{ missing[kind] }} 份未繳交</span>
    </RouterLink>
  </div>
</template>

<style scoped>
.kinds {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 280px));
  justify-content: center;
  gap: 60px;
  margin-top: 40px;
}

/* 平常是淺灰卡片，滑過或鍵盤選到時換成淡綠底（設計稿兩張卡各畫了一次選到的樣子） */
.kind {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  aspect-ratio: 1;
  max-height: 300px;
  border: 1px solid #b9b4ad;
  border-radius: 30px;
  background: #f4f4f3;
  text-align: center;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.kind:hover,
.kind:focus-visible {
  border-color: #9fc07a;
  background: #e9eedf;
}

.kind strong {
  font-size: 22px;
  font-weight: 500;
}

.kind__icon {
  font-size: 38px;
  line-height: 1;
}

.kind__hint {
  color: var(--home-muted);
}

.kind--performance {
  color: #3f8f2a;
}

.kind--quiz {
  color: #1f66b8;
}

.kind__badge {
  position: absolute;
  top: 16px;
  right: 16px;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  background: #d9412f;
  color: #fff;
  font-size: 12px;
}

@media (max-width: 640px) {
  .kinds {
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 20px;
  }

  .kind strong {
    font-size: 18px;
  }

  .kind__hint {
    font-size: 12px;
  }
}
</style>
