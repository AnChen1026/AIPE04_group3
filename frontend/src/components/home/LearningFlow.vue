<script setup lang="ts">
import { computed, ref } from 'vue'
import SectionHeading from './SectionHeading.vue'
import ArrowButton from './ArrowButton.vue'
import type { FlowStep } from '@/mocks/home'

const props = defineProps<{
  studentSteps: FlowStep[]
  teacherSteps: FlowStep[]
}>()

type Role = 'student' | 'teacher'

const roles: { id: Role; label: string }[] = [
  { id: 'student', label: '我是學生' },
  { id: 'teacher', label: '我是老師' },
]

const role = ref<Role>('student')
const steps = computed(() => (role.value === 'student' ? props.studentSteps : props.teacherSteps))
</script>

<template>
  <section id="flow" class="flow" aria-labelledby="flow-title">
    <div class="flow__inner">
      <SectionHeading
        v-reveal
        label="上課流程"
        title="從找課到練習，"
        accent="每一步都清楚"
        heading-id="flow-title"
        align="center"
        tone="dark"
      >
        學生和老師看到的步驟不一樣，切換看看。
      </SectionHeading>

      <div v-reveal="100" class="flow__tabs" role="tablist" aria-label="選擇身分">
        <button
          v-for="item in roles"
          :id="`flow-tab-${item.id}`"
          :key="item.id"
          type="button"
          role="tab"
          :aria-selected="role === item.id"
          aria-controls="flow-panel"
          @click="role = item.id"
        >
          {{ item.label }}
        </button>
      </div>

      <Transition name="flow-swap" mode="out-in">
        <ol
          id="flow-panel"
          :key="role"
          class="flow__list"
          role="tabpanel"
          :aria-labelledby="`flow-tab-${role}`"
        >
          <li v-for="(step, index) in steps" :key="step.title">
            <span class="flow__index">{{ String(index + 1).padStart(2, '0') }}</span>
            <div class="flow__text">
              <h3>{{ step.title }}</h3>
              <p>{{ step.text }}</p>
            </div>
            <span class="flow__tag">{{ step.tag }}</span>
          </li>
        </ol>
      </Transition>

      <div class="flow__action">
        <ArrowButton v-if="role === 'student'" to="/signup" variant="light">註冊開始找課</ArrowButton>
        <ArrowButton v-else to="/signup" variant="light">申請成為老師</ArrowButton>
      </div>
    </div>
  </section>
</template>

<style scoped>
.flow {
  padding: var(--section-space) 0;
  background:
    radial-gradient(circle at 15% 0%, rgba(228, 210, 191, 0.14), transparent 45%),
    var(--home-deep);
  color: var(--home-paper);
}

.flow__inner {
  width: min(880px, calc(100% - 48px));
  margin: 0 auto;
}

.flow__tabs {
  display: flex;
  justify-content: center;
  gap: 6px;
  width: fit-content;
  margin: 36px auto 0;
  padding: 5px;
  border-radius: var(--radius-pill);
  background: rgba(255, 250, 243, 0.08);
}

.flow__tabs button {
  padding: 9px 22px;
  border: 0;
  border-radius: var(--radius-pill);
  background: transparent;
  color: rgba(255, 250, 243, 0.72);
  font-size: 15px;
  cursor: pointer;
  transition: background 0.25s ease, color 0.25s ease;
}

.flow__tabs button[aria-selected='true'] {
  background: var(--home-paper);
  color: var(--home-ink);
}

.flow__list {
  margin: 40px 0 0;
  padding: 8px 28px;
  border-radius: var(--radius-card);
  background: rgba(255, 250, 243, 0.05);
  list-style: none;
}

.flow__list li {
  display: grid;
  grid-template-columns: 56px 1fr auto;
  align-items: start;
  gap: 16px;
  padding: 24px 0;
}

.flow__list li + li {
  border-top: 1px solid rgba(255, 250, 243, 0.12);
}

.flow__index {
  color: var(--home-wood);
  font-family: var(--font-serif);
  font-size: 24px;
  line-height: 1.2;
}

.flow__text h3 {
  margin: 0;
  font-size: 19px;
  font-weight: 500;
}

.flow__text p {
  margin: 6px 0 0;
  color: rgba(255, 250, 243, 0.7);
  font-size: 14px;
  line-height: 1.8;
}

.flow__tag {
  padding: 4px 12px;
  border: 1px solid rgba(255, 250, 243, 0.3);
  border-radius: var(--radius-pill);
  font-size: 12px;
  white-space: nowrap;
}

.flow__action {
  display: flex;
  justify-content: center;
  margin-top: 36px;
}

.flow-swap-enter-active,
.flow-swap-leave-active {
  transition: opacity 0.3s ease, translate 0.3s ease;
}

.flow-swap-enter-from {
  opacity: 0;
  translate: 0 12px;
}

.flow-swap-leave-to {
  opacity: 0;
  translate: 0 -8px;
}

@media (max-width: 640px) {
  .flow__inner {
    width: calc(100% - 32px);
  }

  .flow__list {
    padding: 4px 18px;
  }

  .flow__list li {
    grid-template-columns: 40px 1fr;
  }

  .flow__tag {
    grid-column: 2;
    justify-self: start;
  }
}

@media (prefers-reduced-motion: reduce) {
  .flow-swap-enter-active,
  .flow-swap-leave-active {
    transition: none;
  }
}
</style>
