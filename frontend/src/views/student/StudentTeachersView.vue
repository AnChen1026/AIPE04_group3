<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { fetchMyChangeRequests, joinWithCode } from '@/api/student'
import { useBoundCourses } from '@/composables/useBoundCourses'
import { toneClass } from '@/utils/format'

// 設計稿的「已綁定的老師」：每門已綁定的課一列，可以上課申請或看課表。老師給的綁定碼也在這裡輸入
const router = useRouter()
const courses = useBoundCourses()
const requestCounts = ref<Record<string, number>>({})
const keyword = ref('')
const style = ref('')
const error = ref('')

const code = ref('')
const joining = ref(false)
const joinError = ref('')
const joined = ref<{ courseId: string; title: string } | null>(null)

const styles = computed(() => [...new Set(courses.bound.value.map((item) => item.course_style).filter(Boolean))] as string[])
const courseKeys = computed(() => courses.bound.value.map((item) => item.course_id))
const inquiring = computed(() => courses.conversations.value.filter((item) => !item.bound))
const shown = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return courses.bound.value.filter(
    (item) =>
      (!style.value || item.course_style === style.value) &&
      (!text || [item.teacher_name ?? '', item.course_title ?? ''].some((value) => value.toLowerCase().includes(text))),
  )
})

async function load() {
  try {
    await courses.load()
    const lists = await Promise.all(courses.bound.value.map((item) => fetchMyChangeRequests(item.course_id)))
    requestCounts.value = Object.fromEntries(
      courses.bound.value.map((item, index) => [item.course_id, lists[index]!.filter((row) => row.status === 'pending').length]),
    )
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到老師資料。'
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
    const course = courses.conversations.value.find((item) => item.course_id === result.course_id)
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
  <PageHeader title="已綁定的老師">
    <label class="search-input">
      <span class="visually-hidden">搜尋老師</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋老師" />
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
    </label>
    <RouterLink to="/student/schedule" class="btn btn--primary">申請紀錄</RouterLink>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <form class="card join" novalidate @submit.prevent="join">
    <div class="join__text">
      <h2 class="card__title">輸入綁定碼</h2>
      <p class="muted">老師決定收你之後，會在聊天裡給你一組綁定碼，輸入後就能看課表、交作業。</p>
    </div>
    <div class="join__form">
      <label class="visually-hidden" for="join-code">綁定碼</label>
      <input id="join-code" v-model="code" class="input join__input" placeholder="例如 A8ACE5E2" autocomplete="off" />
      <button type="submit" class="btn btn--primary" :disabled="joining">{{ joining ? '確認中…' : '加入課程' }}</button>
    </div>
    <p v-if="joinError" class="error-text join__error" role="alert">{{ joinError }}</p>
  </form>

  <div v-if="styles.length > 1" class="chip-group teachers__filters" role="group" aria-label="依課程類型篩選">
    <button type="button" class="chip" :aria-pressed="style === ''" @click="style = ''">全部</button>
    <button v-for="item in styles" :key="item" type="button" class="chip" :aria-pressed="style === item" @click="style = item">
      {{ item }}
    </button>
  </div>

  <div v-if="courses.loaded.value && courses.bound.value.length === 0" class="card empty">
    還沒有綁定的老師。到首頁找一門喜歡的課，按「聯繫老師」和老師聊聊，拿到綁定碼後在上面輸入。
  </div>
  <div v-else-if="shown.length === 0 && courses.loaded.value" class="card empty">找不到符合的老師。</div>
  <article
    v-for="item in shown"
    :key="item.id"
    class="tone-card teacher"
    :class="toneClass(item.course_id, courseKeys)"
  >
    <p class="tone-card__cell tone-card__title">{{ item.teacher_name }}老師</p>
    <div class="tone-card__cell teacher__info">
      <p class="tone-card__title">{{ item.course_title }}</p>
      <p class="tone-card__title">已有 {{ requestCounts[item.course_id] ?? 0 }} 筆上課申請</p>
    </div>
    <div class="teacher__actions">
      <RouterLink :to="{ path: '/student/schedule', query: { course: item.course_id, apply: '1' } }" class="tone-btn">上課申請</RouterLink>
      <RouterLink :to="{ path: '/student/schedule', query: { course: item.course_id } }" class="tone-btn">查看課表</RouterLink>
    </div>
  </article>

  <section v-if="inquiring.length" class="card inquiring">
    <h2 class="card__title">洽詢中、還沒綁定</h2>
    <ul>
      <li v-for="item in inquiring" :key="item.id">
        <span>{{ item.teacher_name }} 老師｜{{ item.course_title }}</span>
        <RouterLink :to="`/student/chat/${item.id}`" class="btn btn--ghost btn--small">聊天</RouterLink>
      </li>
    </ul>
  </section>

  <NoticeDialog
    :open="joined !== null"
    :message="`已經加入「${joined?.title ?? ''}」！`"
    detail="現在可以看課表、請假或調課，也能照老師指定的曲子錄音交作業。"
    confirm-text="去交作業"
    cancel-text="留在這裡"
    @confirm="router.push({ path: '/student/homework/practice', query: { course: joined!.courseId } })"
    @cancel="joined = null"
  />
</template>

<style scoped>
.search-input {
  width: min(220px, 100%);
}

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

.teachers__filters {
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 2px solid var(--home-line);
}

.teacher {
  grid-template-columns: 150px minmax(0, 1fr) auto;
}

.teacher__info {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 28px;
}

.teacher__actions {
  display: flex;
  gap: 10px;
}

.inquiring {
  margin-top: 22px;
}

.inquiring ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.inquiring li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-top: 1px solid var(--home-line);
}

.inquiring li:first-child {
  border-top: 0;
}
</style>
