<script setup lang="ts">
import { computed, ref, useSlots } from 'vue'

// 登入註冊頁的欄位：標題、輸入框、錯誤訊息。type="password" 時多一個顯示／隱藏密碼的按鈕。
// 要用 select、textarea 時把控制項放進預設插槽，套 class="auth-input" 即可。
const value = defineModel<string>({ default: '' })

const props = withDefaults(
  defineProps<{
    id: string
    label: string
    type?: string
    autocomplete?: string
    placeholder?: string
    inputmode?: 'text' | 'email' | 'tel' | 'numeric'
    maxlength?: number
    required?: boolean
    error?: string
    hint?: string
  }>(),
  { type: 'text', autocomplete: undefined, placeholder: undefined, inputmode: undefined, maxlength: undefined, error: '', hint: '' },
)

const slots = useSlots()
const shown = ref(false)
const isPassword = computed(() => props.type === 'password')
const inputType = computed(() => (isPassword.value && shown.value ? 'text' : props.type))
const errorId = computed(() => `${props.id}-error`)
</script>

<template>
  <div class="auth-field">
    <label class="auth-field__label" :for="id">
      {{ label }}<span v-if="required" class="auth-field__required" aria-hidden="true">*</span>
    </label>
    <div class="auth-field__control">
      <slot v-if="slots.default" />
      <template v-else>
        <input
          :id="id"
          v-model="value"
          class="auth-input"
          :class="{ 'auth-input--with-toggle': isPassword }"
          :type="inputType"
          :autocomplete="autocomplete"
          :placeholder="placeholder"
          :inputmode="inputmode"
          :maxlength="maxlength"
          :required="required || undefined"
          :aria-invalid="!!error || undefined"
          :aria-describedby="error ? errorId : undefined"
        />
        <button
          v-if="isPassword"
          type="button"
          class="auth-field__toggle"
          :aria-label="shown ? '隱藏密碼' : '顯示密碼'"
          :aria-pressed="shown"
          :aria-controls="id"
          @click="shown = !shown"
        >
          <svg v-if="shown" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true">
            <path d="M3 3l18 18" />
            <path d="M10.6 5.1A9.8 9.8 0 0 1 12 5c5 0 8.5 4.2 9.5 7-.4 1.1-1.2 2.5-2.4 3.8M6.1 6.6C4.3 7.9 3 9.8 2.5 12c1 2.8 4.5 7 9.5 7 1.6 0 3-.4 4.3-1" />
            <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true">
            <path d="M2.5 12C3.5 9.2 7 5 12 5s8.5 4.2 9.5 7c-1 2.8-4.5 7-9.5 7s-8.5-4.2-9.5-7Z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </button>
      </template>
    </div>
    <p v-if="error" :id="errorId" class="auth-field__error">{{ error }}</p>
    <p v-else-if="hint" class="auth-field__hint">{{ hint }}</p>
  </div>
</template>
