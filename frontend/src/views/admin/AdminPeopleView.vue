<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/console/PageHeader.vue'
import { fetchAdminStudents, fetchAdminTeachers } from '@/api/admin'
import { openAdminConversation } from '@/api/support'
import type { CurrentUser } from '@/types/user'
import { formatDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const people = ref<CurrentUser[]>([])
const keyword = ref('')
const error = ref('')

const isTeacher = computed(() => route.name === 'admin-teachers')

const shown = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  if (!text) return people.value
  return people.value.filter((person) =>
    [person.name, person.email, person.phone_number ?? ''].some((value) => value.toLowerCase().includes(text)),
  )
})

// 主動找這位老師或學生聊：沒有對話就先建一段
async function chat(person: CurrentUser) {
  try {
    const conversation = await openAdminConversation(person.id)
    router.push(`/admin/chat/${conversation.id}`)
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '沒有辦法開啟對話。'
  }
}

const applicationText: Record<string, string> = {
  pending: '等待審核',
  approved: '已核准',
  rejected: '已駁回',
}

function sexText(value: string | null) {
  if (value === 'male') return '男'
  if (value === 'female') return '女'
  return '未填'
}

async function load() {
  error.value = ''
  keyword.value = ''
  try {
    people.value = isTeacher.value ? await fetchAdminTeachers() : await fetchAdminStudents()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到名單。'
  }
}

watch(() => route.name, load, { immediate: true })
</script>

<template>
  <PageHeader
    :title="isTeacher ? '老師' : '學生'"
    :description="isTeacher ? '這裡列出所有老師帳號。' : '這裡列出所有學生帳號。'"
  >
    <label class="search-input">
      <span class="visually-hidden">搜尋</span>
      <input v-model="keyword" class="input" type="search" placeholder="搜尋姓名、Email 或電話" />
    </label>
  </PageHeader>
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="shown.length === 0" class="card empty">
    {{ people.length === 0 ? (isTeacher ? '目前沒有老師。' : '目前沒有學生。') : '找不到符合的帳號。' }}
  </div>
  <article v-for="person in shown" :key="person.id" class="card person">
    <div class="person__head">
      <span class="person__avatar" aria-hidden="true">{{ person.name.slice(0, 1) }}</span>
      <div>
        <strong>{{ person.name }}</strong>
        <p class="muted">{{ person.email }}</p>
      </div>
      <span class="person__state">{{ person.is_active ? '已啟用' : '未啟用' }}</span>
      <button v-if="person.is_active" type="button" class="btn btn--ghost btn--small" @click="chat(person)">聊天</button>
    </div>
    <dl class="person__meta">
      <div>
        <dt>電話</dt>
        <dd>{{ person.phone_number || '未填' }}</dd>
      </div>
      <div>
        <dt>生日</dt>
        <dd>{{ person.birthdate ? formatDate(person.birthdate) : '未填' }}</dd>
      </div>
      <div>
        <dt>性別</dt>
        <dd>{{ sexText(person.sex) }}</dd>
      </div>
      <div v-if="isTeacher">
        <dt>審核</dt>
        <dd>{{ person.application_status ? (applicationText[person.application_status] ?? person.application_status) : '尚未申請' }}</dd>
      </div>
    </dl>
  </article>
</template>

<style scoped>
.search-input {
  width: min(260px, 100%);
}

.person__head {
  display: flex;
  align-items: center;
  gap: 14px;
}

.person__avatar {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--home-wood);
  color: var(--home-accent-dark);
  font-family: var(--font-serif);
  font-size: 20px;
}

.person__head .muted {
  margin: 4px 0 0;
}

.person__state {
  margin-left: auto;
  color: var(--home-muted);
  font-size: 13px;
}

.person__meta {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 16px 0 0;
}

.person__meta dt {
  color: var(--home-muted);
  font-size: 13px;
}

.person__meta dd {
  margin: 4px 0 0;
}

@media (max-width: 800px) {
  .person__meta {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
