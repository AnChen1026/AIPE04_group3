import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

// 編輯頁還沒儲存就要離開時，先跳「編輯-未儲存」提示框
export function useLeaveGuard(dirty: Ref<boolean>) {
  const asking = ref(false)
  let answer: ((leave: boolean) => void) | null = null

  onBeforeRouteLeave(() => {
    if (!dirty.value) return true
    asking.value = true
    return new Promise<boolean>((resolve) => {
      answer = resolve
    })
  })

  function decide(leave: boolean) {
    asking.value = false
    answer?.(leave)
    answer = null
  }

  // 關分頁或重新整理時，交給瀏覽器自己的提示
  function beforeUnload(event: BeforeUnloadEvent) {
    if (dirty.value) event.preventDefault()
  }
  onMounted(() => window.addEventListener('beforeunload', beforeUnload))
  onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnload))

  return { asking, leave: () => decide(true), stay: () => decide(false) }
}
