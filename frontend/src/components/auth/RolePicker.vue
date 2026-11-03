<script setup lang="ts">
// 註冊身分：學生／老師，做成一列兩格的切換
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
    <button type="button" role="radio" class="roles__option" :aria-checked="role === 'student'" @click="role = 'student'">
      <strong>{{ studentLabel }}</strong>
      <span v-if="studentHint">{{ studentHint }}</span>
    </button>
    <button type="button" role="radio" class="roles__option" :aria-checked="role === 'teacher'" @click="role = 'teacher'">
      <strong>{{ teacherLabel }}</strong>
      <span v-if="teacherHint">{{ teacherHint }}</span>
    </button>
  </div>
</template>

<style scoped>
.roles {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.roles__option {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  min-height: 52px;
  padding: 12px 16px;
  border: 1px solid var(--home-line);
  border-radius: 12px;
  background: transparent;
  color: var(--home-ink);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.25s ease, background 0.25s ease, color 0.25s ease;
}

.roles__option:hover {
  border-color: var(--home-wood);
  background: var(--home-paper);
}

.roles__option strong {
  font-size: 14.5px;
  font-weight: 500;
}

.roles__option span {
  color: var(--home-muted);
  font-size: 12px;
}

.roles__option[aria-checked='true'] {
  border-color: var(--home-accent);
  background: var(--home-paper);
  box-shadow: inset 0 0 0 1px var(--home-accent);
}

.roles__option[aria-checked='true'] strong {
  color: var(--home-accent-dark);
}

.roles__option:focus-visible {
  outline: 2px solid var(--home-accent);
  outline-offset: 2px;
}

.roles[aria-invalid='true'] .roles__option {
  border-color: #c99280;
}
</style>
