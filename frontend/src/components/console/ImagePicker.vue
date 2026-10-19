<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

// 選一張圖片：先在畫面上預覽，按「儲存」時才上傳。沒有圖片時顯示預設圖。
const file = defineModel<File | null>({ required: true })
const props = defineProps<{
  current: string | null
  fallback: string
  label: string
  shape?: 'circle' | 'wide'
}>()

const error = ref('')
const input = ref<HTMLInputElement | null>(null)
const previewUrl = ref('')

const shown = computed(() => previewUrl.value || props.current || props.fallback)
const isDefault = computed(() => !previewUrl.value && !props.current)

function choose(event: Event) {
  error.value = ''
  const picked = (event.target as HTMLInputElement).files?.[0] ?? null
  if (!picked) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(picked.type)) {
    error.value = '請選擇 JPG、PNG 或 WebP 圖片。'
    return
  }
  if (picked.size > 5 * 1024 * 1024) {
    error.value = '圖片最大 5 MB。'
    return
  }
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = URL.createObjectURL(picked)
  file.value = picked
}

function reset() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  file.value = null
  if (input.value) input.value.value = ''
}

defineExpose({ reset })
onBeforeUnmount(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})
</script>

<template>
  <div class="picker" :class="`picker--${shape ?? 'wide'}`">
    <img :src="shown" :alt="label" class="picker__image" />
    <div class="picker__side">
      <span class="field__label">{{ label }}</span>
      <span class="field__hint">{{ isDefault ? '目前使用預設圖片。' : file ? '儲存後換成這張。' : '已上傳。' }}JPG、PNG、WebP，最大 5 MB。</span>
      <div class="picker__actions">
        <label class="btn btn--ghost btn--small">
          {{ current || file ? '換一張' : '上傳圖片' }}
          <input ref="input" type="file" accept="image/jpeg,image/png,image/webp" class="visually-hidden" @change="choose" />
        </label>
        <button v-if="file" type="button" class="btn btn--small" @click="reset">取消這張</button>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
.picker {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}

.picker__image {
  flex: none;
  object-fit: cover;
  background: var(--home-cream);
}

.picker--circle .picker__image {
  width: 96px;
  height: 96px;
  object-position: center 20%;
  border-radius: 50%;
}

.picker--wide .picker__image {
  width: 220px;
  aspect-ratio: 4 / 3;
  border-radius: 18px;
}

.picker__side {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.picker__actions {
  display: flex;
  gap: 8px;
}

.picker__actions label {
  cursor: pointer;
}
</style>
