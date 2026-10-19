<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { fetchMyConversations, joinWithCode } from '@/api/student'
import type { Conversation } from '@/types/api'
import { formatShort } from '@/utils/format'

const conversations = ref<Conversation[]>([])
const loaded = ref(false)
const error = ref('')
const router = useRouter()

// 老師給的綁定碼：直接在這裡輸入就能加入課程，不用先打開聊天
const code = ref('')
const joining = ref(false)
const joinError = ref('')
const joined = ref<{ courseId: string; title: string } | null>(null)

async function load() {
  try {
    conversations.value = await fetchMyConversations()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到你的課程。'
  } finally {
    loaded.value = true
  }
}

async function join() {
  joinError.value = ''
  if (!code.value.trim()) {
    joinError.value = '請輸入老師給你的綁定碼。'
    return
  }
  joining.value = true
  try {
    const result = await joinWithCode(code.value.trim().toUpperCase())
    code.value = ''
    await load()
    const course = conversations.value.find((item) => item.course_id === result.course_id)
    joined.value = { courseId: result.course_id, title: course?.course_title ?? '這門課' }
  } catch (problem) {
    joinError.value = problem instanceof Error ? problem.message : '綁定失敗，請確認綁定碼。'
  } finally {
    joining.value = false
  }
}

onMounted(load)
</script>

<template>
  <PageHeader title="我的課程" description="洽詢過的課都在這裡。老師給你綁定碼後，在聊天裡輸入就能開始上課。">
    <RouterLink :to="{ path: '/', hash: '#courses' }" class="btn btn--primary">找新課程</RouterLink>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <form class="card join" novalidate @submit.prevent="join">
    <div class="join__text">
      <h2 class="card__title">輸入綁定碼</h2>
      <p class="muted">老師決定收你之後，會在聊天裡給你一組綁定碼，輸入後就能看課表、送練習。</p>
    </div>
    <div class="join__form">
      <label class="visually-hidden" for="join-code">綁定碼</label>
      <input id="join-code" v-model="code" class="input join__input" placeholder="例如 A8ACE5E2" autocomplete="off" />
      <button type="submit" class="btn btn--primary" :disabled="joining">{{ joining ? '確認中…' : '加入課程' }}</button>
    </div>
    <p v-if="joinError" class="error-text join__error" role="alert">{{ joinError }}</p>
  </form>

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

  <NoticeDialog
    :open="joined !== null"
    :message="`已經加入「${joined?.title ?? ''}」！`"
    detail="現在可以看課表、請假或調課，也能照老師指定的曲子錄音練習。"
    confirm-text="去練習"
    cancel-text="留在這裡"
    @confirm="router.push({ path: '/student/practice', query: { course: joined!.courseId } })"
    @cancel="joined = null"
  />
</template>

<style scoped>
.join {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 18px;
  background: var(--home-cream);
}

.join__text p {
  margin: -6px 0 0;
  font-size: 13px;
}

.join__form {
  display: flex;
  gap: 10px;
}

.join__input {
  width: 180px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.join__error {
  flex-basis: 100%;
}

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
