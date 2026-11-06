<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchTeacherForStudent } from '@/api/student'
import { apiUrl } from '@/api/http'
import type { StudentTeacherProfile } from '@/types/api'
import { styleColor } from '@/utils/courseStyle'
import defaultPhoto from '@/assets/images/女老師3.png'

// 學生看老師資料（設計稿「老師-設定-個人資料」的樣子）：上面是照片、姓名、教的風格與年資，
// 下面是老師填的介紹。只看得到自己洽詢過或綁定的老師
const route = useRoute()
const router = useRouter()
const teacher = ref<StudentTeacherProfile | null>(null)
const error = ref('')

const rows = computed(() => {
  const value = teacher.value
  if (!value) return []
  const area = [value.teaching_city, value.teaching_district].filter(Boolean).join(' ')
  return [
    { label: '性別', text: value.gender },
    { label: '專業', text: value.expertise },
    { label: '教學地區', text: area },
    { label: '教學對象', text: value.target_learning },
    { label: '教學方式', text: value.teaching_method },
    { label: '教學風格', text: value.teaching_style },
    { label: '自我介紹', text: value.short_intros },
  ]
})

function back() {
  if (window.history.state?.back) router.back()
  else router.push({ name: 'student-teachers' })
}

onMounted(async () => {
  try {
    teacher.value = await fetchTeacherForStudent(String(route.params.id))
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到老師資料。'
  }
})
</script>

<template>
  <PageHeader title="老師資料">
    <button type="button" class="btn btn--ghost" @click="back">返回</button>
  </PageHeader>
  <p v-if="error" class="error-text" role="alert">{{ error }}</p>

  <template v-if="teacher">
    <section class="card teacher-head">
      <img :src="teacher.photo_url ? apiUrl(teacher.photo_url) : defaultPhoto" :alt="`${teacher.name}老師的照片`" />
      <div class="teacher-head__text">
        <h2>{{ teacher.name }}老師</h2>
        <ul v-if="teacher.course_styles.length" class="teacher-head__tags" aria-label="教的風格">
          <li
            v-for="style in teacher.course_styles"
            :key="style"
            :style="{ background: styleColor(style).bg, color: styleColor(style).ink }"
          >
            {{ style }}
          </li>
        </ul>
        <p v-if="teacher.seniority !== null" class="teacher-head__years">{{ teacher.seniority }} 年教學經驗</p>
      </div>
    </section>

    <dl class="card profile">
      <div v-for="row in rows" :key="row.label" class="profile__row">
        <dt>{{ row.label }}</dt>
        <dd :class="{ muted: !row.text }">{{ row.text || '老師還沒填' }}</dd>
      </div>
    </dl>

    <section class="card courses">
      <h2 class="card__title">和這位老師的課</h2>
      <ul>
        <li v-for="item in teacher.courses" :key="item.course_id">
          <span class="courses__dot" :style="{ background: styleColor(item.course_style).strong }" aria-hidden="true"></span>
          <span>{{ item.course_title }}</span>
          <span class="badge" :class="item.bound ? 'badge--accent' : 'badge--warn'">{{ item.bound ? '進行中' : '洽詢中' }}</span>
          <RouterLink :to="`/student/chat/${item.conversation_id}`" class="btn btn--ghost btn--small courses__chat">聊天</RouterLink>
        </li>
      </ul>
    </section>
  </template>
</template>

<style scoped>
.teacher-head {
  display: flex;
  align-items: center;
  gap: 24px;
}

.teacher-head img {
  flex: none;
  width: 112px;
  height: 112px;
  object-fit: cover;
  object-position: center 20%;
  border-radius: 50%;
}

.teacher-head__text {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.teacher-head h2 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: 24px;
}

.teacher-head__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.teacher-head__tags li {
  padding: 3px 14px;
  border-radius: var(--radius-pill);
  font-size: 14px;
  font-weight: 700;
}

.teacher-head__years {
  margin: 0;
  color: var(--home-muted);
}

.profile {
  margin: 16px 0 0;
}

.profile__row {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr);
  gap: 16px;
  padding: 12px 0;
  border-top: 1px solid var(--home-line);
}

.profile__row:first-child {
  border-top: 0;
}

.profile dt {
  color: var(--home-muted);
  font-size: 14px;
}

.profile dd {
  margin: 0;
  white-space: pre-wrap;
}

.courses {
  margin-top: 16px;
}

.courses ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.courses li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-top: 1px solid var(--home-line);
}

.courses li:first-child {
  border-top: 0;
}

.courses__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.courses__chat {
  margin-left: auto;
}

@media (max-width: 560px) {
  .teacher-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .profile__row {
    grid-template-columns: 1fr;
    gap: 2px;
  }
}
</style>
