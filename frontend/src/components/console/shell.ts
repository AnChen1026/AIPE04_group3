import type { InjectionKey } from 'vue'

// 外框告訴各頁的 PageHeader：按鈕要不要送到上方標題列（老師後台、學生專區才有）
export const SHELL_TOP_ACTIONS: InjectionKey<boolean> = Symbol('shell-top-actions')
