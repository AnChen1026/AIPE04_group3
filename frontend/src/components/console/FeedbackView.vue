<script setup lang="ts">
import type { Recording } from '@/types/api'
import { RECORDING_STATUS_LABELS } from '@/utils/format'

// 一筆練習的回饋：只顯示文字。分數只給 LLM 判斷表現，不給學生和老師看。
defineProps<{ recording: Recording }>()
</script>

<template>
  <div class="feedback">
    <span
      class="badge"
      :class="{
        'badge--accent': recording.status === 'completed',
        'badge--error': recording.status === 'failed',
        'badge--warn': recording.status === 'pending' || recording.status === 'processing',
      }"
    >
      {{ RECORDING_STATUS_LABELS[recording.status] }}
    </span>
    <template v-if="recording.status === 'completed' && recording.feedback">
      <p class="feedback__text">{{ recording.feedback.feedback_text }}</p>
    </template>
    <p v-else-if="recording.status === 'failed'" class="feedback__text feedback__text--failed">
      {{ recording.feedback?.feedback_text || '這次沒有分析成功。' }}（可以再錄一次。）
    </p>
    <p v-else class="feedback__text muted">分析大約需要半分鐘，完成後會自動更新。</p>
  </div>
</template>

<style scoped>
.feedback__text {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.feedback__text--failed {
  color: #9a4a35;
}
</style>
