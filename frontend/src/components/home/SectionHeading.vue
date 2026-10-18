<script setup lang="ts">
// 各區塊共用的標題：小標籤、標題（後半段用襯線字強調）、說明文字
withDefaults(
  defineProps<{
    label: string
    title: string
    accent?: string
    headingId?: string
    align?: 'left' | 'center'
    tone?: 'light' | 'dark'
  }>(),
  { accent: '', headingId: undefined, align: 'left', tone: 'light' },
)
</script>

<template>
  <div class="heading" :class="[`heading--${align}`, `heading--${tone}`]">
    <p class="heading__label">{{ label }}</p>
    <h2 :id="headingId">
      {{ title }}<em v-if="accent">{{ accent }}</em>
    </h2>
    <p v-if="$slots.default" class="heading__text"><slot /></p>
  </div>
</template>

<style scoped>
.heading {
  max-width: 620px;
}

.heading--center {
  margin-inline: auto;
  text-align: center;
}

.heading__label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 5px 14px;
  border-radius: var(--radius-pill);
  background: var(--home-paper);
  color: var(--home-ink);
  font-size: 13px;
  letter-spacing: 0.1em;
}

.heading__label::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--home-accent);
}

.heading h2 {
  margin: 18px 0 0;
  color: var(--home-ink);
  font-size: clamp(28px, 3.4vw, 44px);
  font-weight: 500;
  line-height: 1.3;
  letter-spacing: 0.02em;
  text-wrap: balance;
}

.heading h2 em {
  display: block;
  font-family: var(--font-serif);
  font-style: normal;
  color: var(--home-accent);
}

.heading__text {
  margin: 16px 0 0;
  color: var(--home-muted);
  font-size: 16px;
  line-height: 1.8;
  text-wrap: pretty;
}

.heading--dark .heading__label {
  background: rgba(255, 250, 243, 0.12);
  color: var(--home-paper);
}

.heading--dark .heading__label::before {
  background: var(--home-wood);
}

.heading--dark h2 {
  color: var(--home-paper);
}

.heading--dark h2 em {
  color: var(--home-wood);
}

.heading--dark .heading__text {
  color: rgba(255, 250, 243, 0.72);
}
</style>
