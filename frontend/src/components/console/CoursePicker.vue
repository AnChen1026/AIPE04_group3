<script setup lang="ts">
import type { Conversation } from '@/types/api'

// 學生頁上方選擇要看哪一門已綁定的課
const courseId = defineModel<string>({ required: true })
defineProps<{ courses: Conversation[] }>()
</script>

<template>
  <select v-if="courses.length > 1" v-model="courseId" class="select picker" aria-label="選擇課程">
    <option v-for="item in courses" :key="item.course_id" :value="item.course_id">
      {{ item.course_title }}｜{{ item.teacher_name }} 老師
    </option>
  </select>
  <span v-else-if="courses.length === 1" class="badge badge--soft picker__single">
    {{ courses[0]!.course_title }}｜{{ courses[0]!.teacher_name }} 老師
  </span>
</template>

<style scoped>
.picker {
  width: auto;
  min-width: 220px;
}

.picker__single {
  padding: 8px 16px;
  font-size: 14px;
}
</style>
