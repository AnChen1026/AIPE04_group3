import type { Directive } from 'vue'

// v-reveal：元素捲進畫面時輕輕往上浮現。值是延遲毫秒，方便同一排卡片錯開出現
const observers = new WeakMap<HTMLElement, IntersectionObserver>()

export const vReveal: Directive<HTMLElement, number | undefined> = {
  mounted(element, binding) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    element.classList.add('reveal')
    element.style.transitionDelay = `${binding.value ?? 0}ms`
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return
        element.classList.add('reveal--in')
        observer.disconnect()
      },
      { rootMargin: '0px 0px -10% 0px' },
    )
    observer.observe(element)
    observers.set(element, observer)
  },
  unmounted(element) {
    observers.get(element)?.disconnect()
    observers.delete(element)
  },
}

declare module 'vue' {
  interface ComponentCustomProperties {
    vReveal: typeof vReveal
  }
}
