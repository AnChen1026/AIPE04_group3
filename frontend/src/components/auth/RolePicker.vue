<script setup lang="ts">
// 設計稿上的兩張身分卡：學生／老師
const role = defineModel<'student' | 'teacher' | null>({ required: true })

defineProps<{
  studentLabel: string
  teacherLabel: string
  studentHint?: string
  teacherHint?: string
  invalid?: boolean
}>()
</script>

<template>
  <div class="roles" role="radiogroup" aria-label="選擇身分" :aria-invalid="invalid || undefined">
    <button
      type="button"
      role="radio"
      class="roles__card"
      :aria-checked="role === 'student'"
      @click="role = 'student'"
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
        <circle cx="12" cy="8" r="3.5" />
        <path d="M5 20c0-3.9 3.1-7 7-7s7 3.1 7 7" stroke-linecap="round" />
      </svg>
      <strong>{{ studentLabel }}</strong>
      <span v-if="studentHint">{{ studentHint }}</span>
    </button>
    <button
      type="button"
      role="radio"
      class="roles__card"
      :aria-checked="role === 'teacher'"
      @click="role = 'teacher'"
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
        <path d="M9 18V5l11-2v13" stroke-linecap="round" stroke-linejoin="round" />
        <circle cx="6" cy="18" r="3" />
        <circle cx="17" cy="16" r="3" />
      </svg>
      <strong>{{ teacherLabel }}</strong>
      <span v-if="teacherHint">{{ teacherHint }}</span>
    </button>
  </div>
</template>

<style scoped>
.roles {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 20px 0 6px;
}

.roles__card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 10px;
  border: 1px solid var(--home-line);
  border-radius: 20px;
  background: #fff;
  color: var(--home-ink);
  font: inherit;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.roles__card svg {
  color: var(--home-accent);
}

.roles__card strong {
  font-size: 15px;
  font-weight: 500;
}

.roles__card span {
  color: var(--home-muted);
  font-size: 12px;
}

.roles__card[aria-checked='true'] {
  border-color: var(--home-accent);
  background: var(--home-cream);
  box-shadow: inset 0 0 0 1px var(--home-accent);
}

.roles[aria-invalid='true'] .roles__card {
  border-color: #c9765f;
}
</style>
