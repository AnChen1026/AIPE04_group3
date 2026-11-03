<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/console/PageHeader.vue'
import NoticeDialog from '@/components/console/NoticeDialog.vue'
import ModalPanel from '@/components/console/ModalPanel.vue'
import { dismissPasswordReset, fetchPasswordResets, resetPassword } from '@/api/admin'
import type { PasswordResetRequest } from '@/api/admin'
import { formatDateTime } from '@/utils/format'

// 忘記密碼（地端版本）：使用者在登入頁送出 Email 後出現在這裡，管理員替他重設成臨時密碼。
const requests = ref<PasswordResetRequest[]>([])
const error = ref('')
const pendingAction = ref<{ item: PasswordResetRequest; kind: 'reset' | 'dismiss' } | null>(null)
const result = ref<{ item: PasswordResetRequest; password: string } | null>(null)
const copied = ref(false)

const pendingCount = computed(() => requests.value.filter((item) => item.status === 'pending').length)

const statusText: Record<string, string> = {
  pending: '等待處理',
  completed: '已重設',
  dismissed: '已略過',
}
const roleText: Record<string, string> = { student: '學生', teacher: '老師' }

async function load() {
  error.value = ''
  try {
    requests.value = await fetchPasswordResets()
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '讀不到重設申請。'
  }
}

async function confirmAction() {
  if (!pendingAction.value) return
  const { item, kind } = pendingAction.value
  pendingAction.value = null
  try {
    if (kind === 'reset') {
      const done = await resetPassword(item.id)
      copied.value = false
      result.value = { item, password: done.temporary_password }
    } else {
      await dismissPasswordReset(item.id)
    }
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : '沒有處理成功，請重新整理再試一次。'
  }
  await load()
  window.dispatchEvent(new Event('admin:refresh-badges'))
}

async function copyPassword() {
  if (!result.value) return
  try {
    await navigator.clipboard.writeText(result.value.password)
    copied.value = true
  } catch {
    copied.value = false
  }
}

onMounted(load)
</script>

<template>
  <PageHeader
    title="重設密碼"
    :description="`使用者在「忘記密碼」送出 Email 後會出現在這裡。重設後系統產生一組臨時密碼，只顯示一次，請另外告訴本人。目前 ${pendingCount} 筆等待處理。`"
  />
  <p v-if="error" class="error-text" role="alert">{{ error }}</p>
  <div v-if="requests.length === 0 && !error" class="card empty">目前沒有重設密碼的申請。</div>

  <article v-for="item in requests" :key="item.id" class="card reset" :data-status="item.status">
    <div class="reset__head">
      <span class="reset__avatar" aria-hidden="true">{{ item.user.name.slice(0, 1) }}</span>
      <div class="reset__who">
        <strong>{{ item.user.name }}</strong>
        <p class="muted">{{ item.user.email }} · {{ roleText[item.user.role] ?? item.user.role }}</p>
      </div>
      <span class="reset__status" :data-status="item.status">{{ statusText[item.status] ?? item.status }}</span>
    </div>
    <dl class="reset__body">
      <div>
        <dt>申請時間</dt>
        <dd>{{ formatDateTime(item.created_at) }}</dd>
      </div>
      <div v-if="item.handled_at">
        <dt>處理時間</dt>
        <dd>{{ formatDateTime(item.handled_at) }}</dd>
      </div>
      <div v-if="item.user.auth_provider === 'google'">
        <dt>提醒</dt>
        <dd>這個帳號用 Google 註冊，重設後也能用 Email 和臨時密碼登入。</dd>
      </div>
    </dl>
    <div v-if="item.status === 'pending'" class="reset__actions">
      <button type="button" class="btn btn--ghost btn--small" @click="pendingAction = { item, kind: 'dismiss' }">略過</button>
      <button type="button" class="btn btn--primary btn--small" @click="pendingAction = { item, kind: 'reset' }">重設密碼</button>
    </div>
  </article>

  <NoticeDialog
    :open="pendingAction !== null"
    :message="pendingAction?.kind === 'dismiss' ? `略過 ${pendingAction?.item.user.name ?? ''} 的申請？` : `重設 ${pendingAction?.item.user.name ?? ''} 的密碼？`"
    :detail="pendingAction?.kind === 'dismiss' ? '密碼不會改變。確認不是本人送出的申請時再略過。' : '請先確認是本人提出的申請。重設後舊密碼立刻失效，系統會產生一組臨時密碼。'"
    :confirm-text="pendingAction?.kind === 'dismiss' ? '略過' : '重設'"
    cancel-text="取消"
    :danger="pendingAction?.kind === 'reset'"
    @confirm="confirmAction"
    @cancel="pendingAction = null"
  />

  <ModalPanel :open="result !== null" title="臨時密碼" @close="result = null">
    <template v-if="result">
      <p class="result__intro">已重設 <strong>{{ result.item.user.name }}</strong>（{{ result.item.user.email }}）的密碼。</p>
      <p class="result__password" aria-label="臨時密碼">{{ result.password }}</p>
      <p class="muted result__note">這組密碼只會顯示這一次，關掉後就看不到了。請當面或私訊告訴本人，並提醒他登入後到基本資料確認帳號。</p>
    </template>
    <template #footer>
      <button type="button" class="btn btn--ghost" @click="copyPassword">{{ copied ? '已複製' : '複製密碼' }}</button>
      <button type="button" class="btn btn--primary" @click="result = null">我已經告知本人</button>
    </template>
  </ModalPanel>
</template>

<style scoped>
.reset[data-status='completed'],
.reset[data-status='dismissed'] {
  opacity: 0.72;
}

.reset__head {
  display: flex;
  align-items: center;
  gap: 14px;
}

.reset__avatar {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--home-wood);
  color: var(--home-accent-dark);
  font-family: var(--font-serif);
  font-size: 20px;
}

.reset__who {
  min-width: 0;
}

.reset__who .muted {
  margin: 4px 0 0;
  overflow-wrap: anywhere;
}

.reset__status {
  flex-shrink: 0;
  margin-left: auto;
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  background: var(--home-cream);
  color: var(--home-muted);
  font-size: 13px;
}

.reset__status[data-status='pending'] {
  background: #f6ead7;
  color: var(--home-accent-dark);
}

.reset__status[data-status='completed'] {
  background: #e7f0e4;
  color: #3f6b45;
}

.reset__body {
  display: grid;
  gap: 8px;
  margin: 16px 0 0;
}

.reset__body div {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 8px;
}

.reset__body dt {
  color: var(--home-muted);
}

.reset__body dd {
  margin: 0;
  line-height: 1.7;
}

.reset__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.result__intro {
  margin: 0;
  line-height: 1.7;
}

.result__password {
  margin: 16px 0;
  padding: 16px;
  border: 1px dashed var(--home-wood);
  border-radius: 14px;
  background: var(--home-cream);
  color: var(--home-ink);
  font-family: 'SFMono-Regular', Menlo, Consolas, monospace;
  font-size: 26px;
  letter-spacing: 0.12em;
  text-align: center;
  user-select: all;
}

.result__note {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
}

@media (max-width: 640px) {
  .reset__head {
    flex-wrap: wrap;
  }

  .reset__status {
    margin-left: 0;
  }

  .reset__body div {
    grid-template-columns: 1fr;
    gap: 2px;
  }
}
</style>
