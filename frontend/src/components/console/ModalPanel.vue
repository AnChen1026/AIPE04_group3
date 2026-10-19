<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

// 一般用途的彈出視窗：標題、內容、下方按鈕
const props = defineProps<{ open: boolean; title: string; wide?: boolean }>()
const emit = defineEmits<{ close: [] }>()
const box = ref<HTMLElement | null>(null)

watch(
  () => props.open,
  async (open) => {
    if (open) {
      await nextTick()
      box.value?.focus()
    }
  },
)
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="modal" @click.self="emit('close')" @keydown.esc="emit('close')">
      <div ref="box" class="modal__box" :class="{ 'modal__box--wide': wide }" role="dialog" aria-modal="true" :aria-label="title" tabindex="-1">
        <header class="modal__head">
          <h2>{{ title }}</h2>
          <button type="button" class="modal__close" aria-label="關閉" @click="emit('close')">×</button>
        </header>
        <div class="modal__body"><slot /></div>
        <footer v-if="$slots.footer" class="modal__foot"><slot name="footer" /></footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(62, 52, 44, 0.32);
}

.modal__box {
  display: flex;
  flex-direction: column;
  width: min(520px, 100%);
  max-height: calc(100vh - 32px);
  border-radius: 26px;
  background: var(--home-paper);
  box-shadow: 0 20px 48px rgba(62, 52, 44, 0.2);
  outline: none;
}

.modal__box--wide {
  width: min(720px, 100%);
}

.modal__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 12px;
}

.modal__head h2 {
  margin: 0;
  font-size: 19px;
  font-weight: 500;
}

.modal__close {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--home-muted);
  font-size: 22px;
  cursor: pointer;
}

.modal__close:hover {
  background: var(--home-cream);
}

.modal__body {
  padding: 4px 24px 20px;
  overflow-y: auto;
}

.modal__foot {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px 20px;
  border-top: 1px solid var(--home-line);
}
</style>
