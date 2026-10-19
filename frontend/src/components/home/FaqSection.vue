<script setup lang="ts">
import SectionHeading from './SectionHeading.vue'
import type { FaqItem } from '@/mocks/home'

defineProps<{
  faqs: FaqItem[]
}>()
</script>

<template>
  <section id="faq" class="faq" aria-labelledby="faq-title">
    <SectionHeading v-reveal label="常見問題" title="開始之前" accent="你可能想知道" heading-id="faq-title">
      還有其他問題，可以先聯繫老師，或點右下角的 AI 找課助理
    </SectionHeading>

    <div class="faq__list">
      <details v-for="(item, index) in faqs" :key="item.question" v-reveal="index * 60" :open="index === 0">
        <summary>
          {{ item.question }}
          <span class="faq__icon" aria-hidden="true"></span>
        </summary>
        <p>{{ item.answer }}</p>
      </details>
    </div>
  </section>
</template>

<style scoped>
.faq {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 56px;
  width: min(1160px, calc(100% - 48px));
  margin: 0 auto;
  padding: var(--section-space) 0;
}

.faq__list {
  border-top: 1px solid var(--home-line);
}

.faq details {
  border-bottom: 1px solid var(--home-line);
}

.faq summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 0;
  color: var(--home-ink);
  font-size: 17px;
  cursor: pointer;
  list-style: none;
}

.faq summary::-webkit-details-marker {
  display: none;
}

.faq__icon {
  position: relative;
  flex: none;
  width: 28px;
  height: 28px;
  border: 1px solid var(--home-wood);
  border-radius: 50%;
}

.faq__icon::before,
.faq__icon::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 10px;
  height: 1.5px;
  background: var(--home-accent);
  translate: -50% -50%;
  transition: rotate 0.3s ease;
}

.faq__icon::after {
  rotate: 90deg;
}

.faq details[open] .faq__icon::after {
  rotate: 0deg;
}

.faq details p {
  margin: 0;
  padding: 0 44px 22px 0;
  color: var(--home-muted);
  font-size: 15px;
  line-height: 1.8;
}

@media (max-width: 860px) {
  .faq {
    grid-template-columns: 1fr;
    gap: 32px;
  }
}

@media (max-width: 640px) {
  .faq {
    width: calc(100% - 32px);
  }

  .faq details p {
    padding-right: 0;
  }
}
</style>
