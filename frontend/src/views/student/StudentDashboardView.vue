<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchMyConversations } from '@/api/student'
import type { Conversation } from '@/types/api'
import { formatShort } from '@/utils/format'

const conversations = ref<Conversation[]>([])
const loaded = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    conversations.value = await fetchMyConversations()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到你的課程。'
  } finally {
    loaded.value = true
  }
})
</script>

<template>
  <PageHeader title="我的課程" description="洽詢過的課都在這裡。老師給你綁定碼後，在聊天裡輸入就能開始上課。">
    <RouterLink :to="{ path: '/', hash: '#courses' }" class="btn btn--primary">找新課程</RouterLink>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="loaded && conversations.length === 0" class="card empty">
    還沒有洽詢任何課程。到首頁找一門喜歡的課，按「聯繫老師」就能開始聊。
  </div>

  <div class="courses">
    <article v-for="item in conversations" :key="item.id" class="card course">
      <header class="course__head">
        <div>
          <p class="course__style">{{ item.course_style || '鋼琴課' }}{{ item.course_level ? `・${item.course_level}` : '' }}</p>
          <h2>{{ item.course_title }}</h2>
          <p class="muted">{{ item.teacher_name }} 老師</p>
        </div>
        <span class="badge" :class="item.bound ? 'badge--accent' : 'badge--muted'">{{ item.bound ? '上課中' : '洽詢中' }}</span>
      </header>

      <RouterLink :to="`/student/chat/${item.id}`" class="course__message" :class="{ 'course__message--unread': item.unread_count }">
        <span>{{ item.last_message ?? '還沒有訊息，先跟老師打聲招呼。' }}</span>
        <span class="course__time">
          <template v-if="item.unread_count">{{ item.unread_count }} 則未讀・</template>{{ formatShort(item.last_message_at) }}
        </span>
      </RouterLink>

      <footer class="course__actions">
        <RouterLink :to="`/student/chat/${item.id}`" class="btn btn--ghost btn--small">聊天</RouterLink>
        <template v-if="item.bound">
          <RouterLink :to="{ path: '/student/schedule', query: { course: item.course_id } }" class="btn btn--ghost btn--small">課表</RouterLink>
          <RouterLink :to="{ path: '/student/practice', query: { course: item.course_id } }" class="btn btn--primary btn--small">去練習</RouterLink>
        </template>
        <span v-else class="muted course__hint">綁定後才能看課表、送練習</span>
      </footer>
    </article>
  </div>
</template>

<style scoped>
.courses {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.courses .card + .card {
  margin-top: 0;
}

.course {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.course__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.course__head h2 {
  margin: 2px 0 0;
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 600;
}

.course__head p {
  margin: 0;
  font-size: 13px;
}

.course__style {
  color: var(--home-accent);
}

.course__message {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 16px;
  background: var(--home-bg);
  font-size: 14px;
}

.course__message span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course__message--unread {
  background: var(--home-cream);
  font-weight: 500;
}

.course__time {
  color: var(--home-muted);
  font-size: 12px;
  font-weight: 400;
}

.course__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: auto;
}

.course__hint {
  font-size: 12px;
}
</style>
