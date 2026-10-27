<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import ConsoleIcon from '@/components/console/ConsoleIcon.vue'
import { fetchPublishedCourses } from '@/api/courses'
import { useBoundCourses } from '@/composables/useBoundCourses'
import type { CourseSummary } from '@/types/course'
import { deliveryText, priceText } from '@/utils/format'

// 設計稿的「課程資訊」：洽詢過的課，已綁定的是「進行中」，還在洽詢的是「待確認」。課程內容取自首頁的已發布課程
const courses = useBoundCourses()
const details = ref<CourseSummary[]>([])
const keyword = ref('')
const status = ref<'all' | 'bound' | 'pending'>('all')
const error = ref('')

const filters = [
  { value: 'all', label: '全部' },
  { value: 'bound', label: '進行中' },
  { value: 'pending', label: '待確認' },
] as const

const shown = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return courses.conversations.value
    .filter(
      (item) =>
        (status.value === 'all' || (status.value === 'bound') === Boolean(item.bound)) &&
        (!text || [item.course_title ?? '', item.teacher_name ?? ''].some((value) => value.toLowerCase().includes(text))),
    )
    .map((item) => ({ conversation: item, detail: details.value.find((course) => course.id === item.course_id) ?? null }))
})

onMounted(async () => {
  try {
    ;[details.value] = await Promise.all([fetchPublishedCourses(), courses.load()])
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到課程。'
  }
})
</script>

<template>
  <PageHeader title="課程資訊">
    <label class="search-input">
      <span class="visually-hidden">搜尋課程</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋課程" />
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
    </label>
  </PageHeader>

  <div class="chip-group courses__filters" role="group" aria-label="依狀態篩選">
    <button
      v-for="filter in filters"
      :key="filter.value"
      type="button"
      class="chip"
      :aria-pressed="status === filter.value"
      @click="status = filter.value"
    >
      {{ filter.label }}
    </button>
  </div>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="courses.loaded.value && shown.length === 0" class="card empty">
    {{ courses.conversations.value.length === 0 ? '還沒有洽詢任何課程。到首頁找一門喜歡的課，按「聯繫老師」就能開始聊。' : '沒有符合的課程。' }}
  </div>
  <article v-for="{ conversation, detail } in shown" :key="conversation.id" class="card course">
    <header class="course__head">
      <h2>{{ conversation.course_title }}</h2>
      <RouterLink :to="`/student/chat/${conversation.id}`" class="btn btn--ghost btn--small">查看老師</RouterLink>
    </header>
    <ul class="course__meta">
      <li><ConsoleIcon name="calendar" :size="18" />{{ detail?.timeSlots || '時段和老師討論' }}</li>
      <li><ConsoleIcon name="courses" :size="18" />{{ deliveryText(detail?.deliveryMode) }}{{ detail?.region ? `・${detail.region}` : '' }}</li>
      <li>{{ priceText(detail?.pricePerLesson) }}</li>
    </ul>
    <p class="course__intro">
      <span>課程介紹：</span>
      {{ detail?.description || `${conversation.teacher_name} 老師的${conversation.course_style || '鋼琴'}課${conversation.course_level ? `（${conversation.course_level}）` : ''}。` }}
    </p>
    <span class="badge course__status" :class="conversation.bound ? 'badge--accent' : 'badge--warn'">
      {{ conversation.bound ? '進行中' : '待確認' }}
    </span>
  </article>
</template>

<style scoped>
.search-input {
  width: min(220px, 100%);
}

.courses__filters {
  margin-bottom: 18px;
}

.course {
  position: relative;
  max-width: 640px;
  padding: 22px 30px 26px;
  border-width: 2px;
  border-radius: 40px;
}

.course__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--home-line);
}

.course__head h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.course__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 28px;
  margin: 14px 0 10px;
  padding: 0;
  list-style: none;
}

.course__meta li {
  display: flex;
  align-items: center;
  gap: 8px;
}

.course__intro {
  margin: 0;
  padding-right: 80px;
  line-height: 1.6;
}

.course__intro span {
  display: block;
}

.course__status {
  position: absolute;
  right: 26px;
  bottom: 20px;
}

@media (max-width: 640px) {
  .course__intro {
    padding-right: 0;
  }

  .course__status {
    position: static;
    margin-top: 12px;
  }
}
</style>
