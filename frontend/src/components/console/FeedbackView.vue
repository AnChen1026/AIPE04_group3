<script setup lang="ts">
import type { Recording } from '@/types/api'
import { RECORDING_STATUS_LABELS } from '@/utils/format'

// 一筆練習的回饋：音高、節奏分數與文字。分析失敗時不顯示 0 分。
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
      <div class="feedback__scores">
        <span>音高 <strong>{{ recording.feedback.pitch_score }}</strong><small> / 70</small></span>
        <span>節奏 <strong>{{ recording.feedback.rhythm_score }}</strong><small> / 30</small></span>
      </div>
      <p class="feedback__text">{{ recording.feedback.feedback_text }}</p>
    </template>
    <p v-else-if="recording.status === 'failed'" class="feedback__text feedback__text--failed">
      {{ recording.feedback?.feedback_text || '這次沒有分析成功。' }}（這不是 0 分，可以再錄一次。）
    </p>
    <p v-else class="feedback__text muted">分析大約需要半分鐘，完成後會自動更新。</p>
  </div>
</template>

<style scoped>
.feedback__scores {
  display: flex;
  gap: 18px;
  margin-top: 8px;
}

.feedback__scores strong {
  color: var(--home-accent-dark);
  font-family: var(--font-serif);
  font-size: 22px;
}

.feedback__scores small {
  color: var(--home-muted);
}

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
