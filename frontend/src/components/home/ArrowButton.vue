<script setup lang="ts">
import { computed } from 'vue'
import type { RouteLocationRaw } from 'vue-router'

// 膠囊按鈕，右側帶一個圓形箭頭。給 to 時是連結，給 href 時是頁內錨點，都沒有時是按鈕
const props = withDefaults(
  defineProps<{
    to?: RouteLocationRaw
    href?: string
    variant?: 'solid' | 'outline' | 'light'
  }>(),
  { to: undefined, href: undefined, variant: 'solid' },
)

const tag = computed(() => (props.to ? 'RouterLink' : props.href ? 'a' : 'button'))
</script>

<template>
  <component
    :is="tag"
    class="arrow-button"
    :class="`arrow-button--${variant}`"
    :to="to"
    :href="href"
    :type="tag === 'button' ? 'button' : undefined"
  >
    <span><slot /></span>
    <span class="arrow-button__icon" aria-hidden="true">
      <svg viewBox="0 0 16 16" width="14" height="14">
        <path d="M4 12 12 4M6 4h6v6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </span>
  </component>
</template>

<style scoped>
.arrow-button {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 6px 6px 6px 20px;
  border: 1px solid transparent;
  border-radius: var(--radius-pill);
  font-size: 15px;
  cursor: pointer;
  transition: background 0.25s ease, color 0.25s ease, border-color 0.25s ease;
}

.arrow-button__icon {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

.arrow-button:hover .arrow-button__icon {
  transform: rotate(45deg);
}

.arrow-button--solid {
  background: var(--home-accent);
  color: var(--home-paper);
}

.arrow-button--solid .arrow-button__icon {
  background: var(--home-paper);
  color: var(--home-accent);
}

.arrow-button--solid:hover {
  background: var(--home-accent-dark);
}

.arrow-button--outline {
  border-color: var(--home-wood);
  background: transparent;
  color: var(--home-ink);
}

.arrow-button--outline .arrow-button__icon {
  background: var(--home-cream);
  color: var(--home-accent);
}

.arrow-button--outline:hover {
  border-color: var(--home-accent);
}

.arrow-button--light {
  background: var(--home-paper);
  color: var(--home-ink);
}

.arrow-button--light .arrow-button__icon {
  background: var(--home-accent);
  color: var(--home-paper);
}

@media (prefers-reduced-motion: reduce) {
  .arrow-button:hover .arrow-button__icon {
    transform: none;
  }
}
</style>
