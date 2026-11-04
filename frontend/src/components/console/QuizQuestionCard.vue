<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { QUIZ_DIFFICULTY_LABELS, QUIZ_TYPE_LABELS, optionLetter, optionLetters } from '@/utils/format'

// 設計稿的一題卡片：題型、難易度、第幾題、單元、題目、A～D 選項，下面一顆展開按鈕，最下面上一題／下一題。
// preview：老師預覽 AI 出的題，按鈕是「查看答案及解析」。
// answer：學生作答，可以點選項（多選題可以選多個），按鈕是「查看提示」。
// editable（只用在 preview）：老師審查時直接點選項改正確答案，綠色就是目前的答案。
const props = defineProps<{
  mode: 'preview' | 'answer'
  index: number
  total: number
  type: string
  difficulty: string | null
  topic: string | null
  question: string
  options: string[]
  answers?: number[]
  explanation?: string | null
  hint?: string | null
  editable?: boolean
}>()
const selected = defineModel<number[]>('selected', { default: () => [] })
const emit = defineEmits<{ prev: []; next: []; 'update:answers': [answers: number[]] }>()

const opened = ref(false)
watch(
  () => props.index,
  () => (opened.value = false),
)

const multiple = computed(() => props.type === 'multiple')

function choose(option: number) {
  if (props.mode === 'preview' && props.editable) {
    const current = props.answers ?? []
    if (!multiple.value) emit('update:answers', [option])
    else emit('update:answers', current.includes(option) ? current.filter((value) => value !== option) : [...current, option].sort())
    return
  }
  if (props.mode !== 'answer') return
  if (!multiple.value) {
    selected.value = [option]
    return
  }
  selected.value = selected.value.includes(option)
    ? selected.value.filter((value) => value !== option)
    : [...selected.value, option].sort()
}

function optionState(option: number) {
  if (props.mode === 'preview' && (opened.value || props.editable) && props.answers?.includes(option)) return 'correct'
  if (props.mode === 'answer' && selected.value.includes(option)) return 'chosen'
  return ''
}
</script>

<template>
  <article class="quiz-card">
    <header class="quiz-card__head">
      <span class="quiz-card__chip">{{ QUIZ_TYPE_LABELS[type] ?? type }}</span>
      <span v-if="difficulty" class="quiz-card__chip">{{ QUIZ_DIFFICULTY_LABELS[difficulty] ?? difficulty }}</span>
      <span class="quiz-card__count">{{ index + 1 }} / {{ total }}</span>
    </header>
    <p v-if="topic" class="quiz-card__topic">{{ topic }}</p>
    <h3 class="quiz-card__question">{{ question }}</h3>
    <p v-if="mode === 'answer' && multiple" class="quiz-card__note">可以選多個答案</p>
    <p v-if="editable" class="quiz-card__note quiz-card__note--edit">點選項改正確答案{{ multiple ? '（多選題至少要兩個）' : '' }}</p>

    <div class="quiz-card__options" :role="mode === 'answer' ? (multiple ? 'group' : 'radiogroup') : undefined" :aria-label="question">
      <button
        v-for="(option, position) in options"
        :key="position"
        type="button"
        class="quiz-option"
        :class="optionState(position) && `quiz-option--${optionState(position)}`"
        :role="mode === 'answer' ? (multiple ? 'checkbox' : 'radio') : undefined"
        :aria-checked="mode === 'answer' ? selected.includes(position) : undefined"
        :disabled="mode !== 'answer' && !editable"
        @click="choose(position)"
      >
        <span class="quiz-option__letter">{{ optionLetter(position) }}</span>
        <span>{{ option }}</span>
      </button>
    </div>

    <button
      v-if="mode === 'preview' || hint"
      type="button"
      class="quiz-card__toggle"
      :aria-expanded="opened"
      @click="opened = !opened"
    >
      {{ mode === 'preview' ? (opened ? '收起答案及解析' : '查看答案及解析') : opened ? '收起提示' : '查看提示' }}
    </button>
    <div v-if="opened" class="quiz-card__reveal" role="status">
      <template v-if="mode === 'preview'">
        <p><strong>答案：</strong>{{ optionLetters(answers ?? []) }}</p>
        <p v-if="explanation"><strong>解析：</strong>{{ explanation }}</p>
        <p v-if="hint" class="muted"><strong>給學生的提示：</strong>{{ hint }}</p>
      </template>
      <p v-else>{{ hint }}</p>
    </div>

    <footer class="quiz-card__nav">
      <button type="button" class="quiz-card__step" :disabled="index === 0" @click="emit('prev')">‹ 上一題</button>
      <button type="button" class="quiz-card__step" :disabled="index >= total - 1" @click="emit('next')">下一題 ›</button>
    </footer>
  </article>
</template>

<style scoped>
.quiz-card {
  padding: 18px 22px 14px;
  border: 1px solid var(--home-line);
  border-radius: 22px;
  background: var(--home-paper);
}

.quiz-card__head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quiz-card__chip {
  padding: 2px 12px;
  border: 1px solid var(--home-wood);
  border-radius: var(--radius-pill);
  font-size: 13px;
}

.quiz-card__count {
  margin-left: auto;
  color: var(--home-muted);
  font-size: 13px;
}

.quiz-card__topic {
  margin: 12px 0 0;
  color: var(--home-muted);
  font-size: 13px;
}

.quiz-card__question {
  margin: 4px 0 0;
  font-size: 17px;
  line-height: 1.6;
}

.quiz-card__note {
  margin: 4px 0 0;
  color: var(--home-muted);
  font-size: 13px;
}

.quiz-card__note--edit {
  color: var(--home-accent);
}

.quiz-card__options {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.quiz-option {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 46px;
  padding: 6px 16px;
  border: 1px solid var(--home-wood);
  border-radius: var(--radius-pill);
  background: #fff;
  color: var(--home-ink);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.quiz-option:disabled {
  cursor: default;
}

.quiz-option:not(:disabled):hover {
  border-color: var(--home-accent);
}

.quiz-option__letter {
  display: inline-grid;
  flex: none;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: 50%;
  background: var(--home-cream);
  font-weight: 700;
}

.quiz-option--chosen {
  border-color: var(--home-accent);
  background: var(--home-cream);
}

.quiz-option--chosen .quiz-option__letter {
  background: var(--home-accent);
  color: var(--home-paper);
}

.quiz-option--correct {
  border-color: #9fc07a;
  background: #e9eedf;
  color: #3f6f2a;
}

.quiz-card__toggle {
  display: block;
  width: 100%;
  min-height: 40px;
  margin-top: 14px;
  border: 1px solid var(--home-wood);
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--home-muted);
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

.quiz-card__toggle:hover {
  border-color: var(--home-accent);
  color: var(--home-ink);
}

.quiz-card__reveal {
  margin-top: 10px;
  padding: 12px 16px;
  border-radius: 16px;
  background: var(--home-cream);
  font-size: 14px;
  line-height: 1.7;
}

.quiz-card__reveal p {
  margin: 0;
}

.quiz-card__reveal p + p {
  margin-top: 6px;
}

.quiz-card__nav {
  display: flex;
  justify-content: space-between;
  margin-top: 18px;
}

.quiz-card__step {
  padding: 4px 0;
  border: 0;
  background: none;
  color: var(--home-muted);
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

.quiz-card__step:disabled {
  cursor: default;
  opacity: 0.4;
}
</style>
