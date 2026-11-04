<script setup lang="ts">
import type { QuizWrongAnswer } from '@/types/api'
import { optionLetter } from '@/utils/format'

// 設計稿「錯誤題目與解析」：每題列出題目、學生作答（紅）、正確答案（綠）、題目解析
defineProps<{ items: QuizWrongAnswer[]; who?: string }>()

function texts(item: QuizWrongAnswer, indexes: number[]) {
  return indexes.map((index) => `${optionLetter(index)}. ${item.options[index] ?? ''}`).join('、')
}
</script>

<template>
  <p v-if="items.length === 0" class="card empty">這次全部答對，沒有錯題。</p>
  <article v-for="item in items" :key="item.question_id" class="wrong">
    <h3 class="wrong__title">第 {{ item.position }} 題<template v-if="item.topic">｜{{ item.topic }}</template></h3>
    <p class="wrong__question">題目：{{ item.question }}</p>
    <p class="wrong__answer wrong__answer--mine">{{ who ?? '學生' }}作答：{{ texts(item, item.selected) }}</p>
    <p class="wrong__answer wrong__answer--right">正確答案：{{ texts(item, item.answers) }}</p>
    <div v-if="item.explanation" class="wrong__explain">
      <strong>題目解析</strong>
      <p>{{ item.explanation }}</p>
    </div>
  </article>
</template>

<style scoped>
.wrong {
  padding: 18px 22px;
  border: 1px solid var(--home-line);
  border-radius: 22px;
  background: #f7f4f0;
}

.wrong + .wrong {
  margin-top: 16px;
}

.wrong__title {
  margin: 0;
  font-size: 17px;
}

.wrong__question {
  margin: 10px 0 0;
}

.wrong__answer {
  margin: 10px 0 0;
  padding: 8px 16px;
  border-radius: var(--radius-pill);
}

.wrong__answer--mine {
  background: #f8d4d4;
  color: #c0392b;
}

.wrong__answer--right {
  background: #e9eedf;
  color: #3f8f2a;
}

.wrong__explain {
  margin-top: 12px;
  font-size: 14px;
  line-height: 1.7;
}

.wrong__explain p {
  margin: 2px 0 0;
}
</style>
