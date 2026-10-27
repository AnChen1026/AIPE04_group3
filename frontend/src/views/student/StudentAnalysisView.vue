<script setup lang="ts">
import PageHeader from '@/components/console/PageHeader.vue'

// 設計稿的「作業分析」入口：演奏作業看每次錄音的音高、節奏與回饋；題庫作業（錯題、答案、解析）由組員的 AI 測驗負責，先留位置
</script>

<template>
  <PageHeader title="作業分析">
    <RouterLink to="/student/homework" class="btn btn--primary">返回</RouterLink>
  </PageHeader>

  <div class="kinds">
    <RouterLink :to="{ path: '/student/homework', query: {} }" class="kind kind--play">
      <span class="kind__icon" aria-hidden="true">♪</span>
      <strong>演奏作業</strong>
      <span class="kind__hint">音高 · 節奏 · 回饋</span>
    </RouterLink>
    <div class="kind kind--quiz" aria-disabled="true">
      <span class="kind__icon" aria-hidden="true">☰</span>
      <strong>題庫作業</strong>
      <span class="kind__hint">錯題 · 答案 · 解析</span>
      <span class="badge badge--muted">尚未開放</span>
    </div>
  </div>
</template>

<style scoped>
.kinds {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 280px));
  gap: 60px;
  margin-top: 40px;
}

.kind {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  aspect-ratio: 1;
  max-height: 300px;
  border: 1px solid var(--home-line);
  border-radius: 30px;
  background: var(--home-paper);
  text-align: center;
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

.kind--play {
  border-color: #9fc07a;
  background: #e9eedf;
  color: #3f8f2a;
  transition: filter 0.2s ease;
}

.kind--play:hover {
  filter: brightness(0.97);
}

.kind--quiz {
  border-color: #b9b4ad;
  background: #f4f4f3;
  color: #1f66b8;
}

@media (max-width: 640px) {
  .kinds {
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
}
</style>
