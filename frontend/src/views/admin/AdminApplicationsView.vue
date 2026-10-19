<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import { approveApplication, fetchApplications, proofUrl, rejectApplication } from '@/api/admin'
import type { TeacherApplication } from '@/api/admin'
import { formatDate } from '@/utils/format'

const applications = ref<TeacherApplication[]>([])
const error = ref('')
const pendingAction = ref<{ item: TeacherApplication; kind: 'approve' | 'reject' } | null>(null)

const shown = computed(() =>
  [...applications.value].sort((a, b) => Number(a.status !== 'pending') - Number(b.status !== 'pending')),
)

const statusText: Record<string, string> = {
  pending: '等待審核',
  approved: '已核准',
  rejected: '已駁回',
}

async function load() {
  try {
    applications.value = await fetchApplications()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到老師申請。'
  }
}

async function confirmAction() {
  if (!pendingAction.value) return
  const { item, kind } = pendingAction.value
  pendingAction.value = null
  try {
    if (kind === 'approve') await approveApplication(item.id)
    else await rejectApplication(item.id)
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '審核沒有完成。'
  }
  await load()
}

onMounted(load)
</script>

<template>
  <PageHeader title="老師申請" description="核准後，老師可以進入老師後台。駁回後，老師會看到未通過。" />
  <p v-if="error" class="error-text">{{ error }}</p>

  <div v-if="shown.length === 0" class="card empty">目前沒有老師申請。</div>
  <article v-for="item in shown" :key="item.id" class="card application">
    <div class="application__head">
      <span class="application__avatar" aria-hidden="true">{{ item.user.name.slice(0, 1) }}</span>
      <div>
        <strong>{{ item.user.name }}</strong>
        <p class="muted">{{ item.user.email }} · {{ formatDate(item.created_at) }}</p>
      </div>
      <span class="application__status" :data-status="item.status">{{ statusText[item.status] ?? item.status }}</span>
    </div>
    <dl class="application__body">
      <div>
        <dt>教學項目</dt>
        <dd>{{ item.teaching_subjects }}</dd>
      </div>
      <div>
        <dt>經歷</dt>
        <dd>{{ item.teaching_experience }}</dd>
      </div>
      <div>
        <dt>簡介</dt>
        <dd>{{ item.bio }}</dd>
      </div>
    </dl>
    <div class="application__actions">
      <a v-if="item.has_proof" class="btn btn--ghost btn--small" :href="proofUrl(item.id)">下載證明文件</a>
      <span v-else class="muted">未上傳證明文件</span>
      <button
        v-if="item.status !== 'approved'"
        type="button"
        class="btn btn--primary btn--small"
        @click="pendingAction = { item, kind: 'approve' }"
      >
        核准
      </button>
      <button
        v-if="item.status === 'pending'"
        type="button"
        class="btn btn--danger btn--small"
        @click="pendingAction = { item, kind: 'reject' }"
      >
        駁回
      </button>
    </div>
  </article>

  <NoticeDialog
    :open="pendingAction !== null"
    :message="pendingAction?.kind === 'reject' ? `駁回 ${pendingAction?.item.user.name ?? ''} 的申請？` : `核准 ${pendingAction?.item.user.name ?? ''} 的申請？`"
    :detail="pendingAction?.kind === 'reject' ? '老師會看到這次申請沒有通過。' : '核准後老師就能進入老師後台。'"
    :confirm-text="pendingAction?.kind === 'reject' ? '駁回' : '核准'"
    cancel-text="取消"
    :danger="pendingAction?.kind === 'reject'"
    @confirm="confirmAction"
    @cancel="pendingAction = null"
  />
</template>

<style scoped>
.application__head {
  display: flex;
  align-items: center;
  gap: 14px;
}

.application__avatar {
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

.application__head .muted {
  margin: 4px 0 0;
}

.application__status {
  margin-left: auto;
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  background: var(--home-cream);
  color: var(--home-muted);
  font-size: 13px;
}

.application__status[data-status='pending'] {
  background: #f6ead7;
  color: var(--home-accent-dark);
}

.application__status[data-status='approved'] {
  background: #e7f0e4;
  color: #3f6b45;
}

.application__body {
  display: grid;
  gap: 10px;
  margin: 16px 0 0;
}

.application__body div {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 8px;
}

.application__body dt {
  color: var(--home-muted);
}

.application__body dd {
  margin: 0;
  line-height: 1.7;
}

.application__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
}

@media (max-width: 640px) {
  .application__status {
    margin-left: 0;
  }

  .application__body div {
    grid-template-columns: 1fr;
    gap: 2px;
  }
}
</style>
