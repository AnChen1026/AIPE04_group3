<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import ConsoleIcon from '@/components/console/ConsoleIcon.vue'
import { fetchAdminStudents, fetchAdminTeachers, fetchApplications } from '@/api/admin'
import type { TeacherApplication } from '@/api/admin'
import type { CurrentUser } from '@/types/user'

const applications = ref<TeacherApplication[]>([])
const teachers = ref<CurrentUser[]>([])
const students = ref<CurrentUser[]>([])
const loading = ref(true)
const error = ref('')

const pending = computed(() => applications.value.filter((item) => item.status === 'pending'))

onMounted(async () => {
  try {
    ;[applications.value, teachers.value, students.value] = await Promise.all([
      fetchApplications(),
      fetchAdminTeachers(),
      fetchAdminStudents(),
    ])
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到管理員資料。'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <PageHeader title="資訊總覽" description="待審核的老師申請，以及目前的老師與學生人數。" />
  <p v-if="error" class="error-text">{{ error }}</p>

  <div class="stats">
    <RouterLink to="/admin/applications" class="card stat">
      <span class="stat__label"><ConsoleIcon name="clipboard" />待審核申請</span>
      <strong>{{ loading ? '—' : pending.length }}<small>筆</small></strong>
    </RouterLink>
    <RouterLink to="/admin/teachers" class="card stat">
      <span class="stat__label"><ConsoleIcon name="students" />老師</span>
      <strong>{{ loading ? '—' : teachers.length }}<small>位</small></strong>
    </RouterLink>
    <RouterLink to="/admin/students" class="card stat">
      <span class="stat__label"><ConsoleIcon name="users" />學生</span>
      <strong>{{ loading ? '—' : students.length }}<small>位</small></strong>
    </RouterLink>
  </div>

  <section class="card">
    <h2 class="card__title"><ConsoleIcon name="clipboard" />待處理事項</h2>
    <ul v-if="!loading" class="todo">
      <li v-for="item in pending" :key="item.id">
        <RouterLink to="/admin/applications">{{ item.user.name }} 的老師申請等待審核</RouterLink>
      </li>
      <li v-if="pending.length === 0" class="muted">目前沒有待審核的老師申請。</li>
    </ul>
  </section>
</template>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stats .card + .card {
  margin-top: 0;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color 0.2s ease;
}

.stat:hover {
  border-color: var(--home-wood);
}

.stat__label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--home-muted);
  font-size: 14px;
}

.stat__label svg {
  color: var(--home-accent);
}

.stat strong {
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: 40px;
  font-weight: 600;
  text-align: center;
}

.stat small {
  margin-left: 4px;
  font-family: var(--font-sans);
  font-size: 16px;
  font-weight: 400;
}

.card__title svg {
  color: var(--home-accent);
}

.todo {
  margin: 0;
  padding-left: 20px;
  line-height: 2;
}

.todo a:hover {
  color: var(--home-accent);
}

@media (max-width: 800px) {
  .stats {
    grid-template-columns: 1fr;
  }
}
</style>
