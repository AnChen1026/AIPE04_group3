<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

// 設計稿的提示框：「更新成功！」「尚未儲存，確定離開？」等。
// 只有 confirmText 時是通知；有 cancelText 時是二選一。
const props = defineProps<{
  open: boolean
  message: string
  detail?: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
}>()

const emit = defineEmits<{ confirm: []; cancel: [] }>()
const confirmButton = ref<HTMLButtonElement | null>(null)

watch(
  () => props.open,
  async (open) => {
    if (open) {
      await nextTick()
      confirmButton.value?.focus()
    }
  },
)
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="notice" @click.self="emit('cancel')" @keydown.esc="emit('cancel')">
      <div class="notice__box" role="alertdialog" aria-modal="true" :aria-label="message">
        <p class="notice__message">{{ message }}</p>
        <p v-if="detail" class="notice__detail">{{ detail }}</p>
        <div class="notice__actions">
          <button v-if="cancelText" type="button" class="btn btn--ghost" @click="emit('cancel')">{{ cancelText }}</button>
          <button
            ref="confirmButton"
            type="button"
            class="btn"
            :class="danger ? 'btn--danger' : 'btn--primary'"
            @click="emit('confirm')"
          >
            {{ confirmText ?? '確認' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.notice {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(62, 52, 44, 0.32);
}

.notice__box {
  width: min(360px, 100%);
  padding: 28px 26px 22px;
  border-radius: 24px;
  background: var(--home-paper);
  box-shadow: 0 20px 48px rgba(62, 52, 44, 0.2);
  text-align: center;
}

.notice__message {
  margin: 0;
  color: var(--home-ink);
  font-size: 17px;
}

.notice__detail {
  margin: 8px 0 0;
  color: var(--home-muted);
  font-size: 14px;
  line-height: 1.7;
}

.notice__actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 20px;
}
</style>
