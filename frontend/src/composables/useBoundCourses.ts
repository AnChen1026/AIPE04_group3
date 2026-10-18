import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchMyConversations } from '@/api/student'
import type { Conversation } from '@/types/api'

// 學生已綁定的課程，從接洽對話整理出來。課表與練習頁用網址上的 ?course= 記住目前選的課。
export function useBoundCourses() {
  const route = useRoute()
  const router = useRouter()
  const conversations = ref<Conversation[]>([])
  const loaded = ref(false)

  const bound = computed(() => conversations.value.filter((item) => item.bound))
  const courseId = computed({
    get: () => {
      const wanted = typeof route.query.course === 'string' ? route.query.course : ''
      return bound.value.some((item) => item.course_id === wanted) ? wanted : (bound.value[0]?.course_id ?? '')
    },
    set: (value: string) => {
      router.replace({ query: { ...route.query, course: value } })
    },
  })
  const current = computed(() => bound.value.find((item) => item.course_id === courseId.value) ?? null)

  async function load() {
    conversations.value = await fetchMyConversations()
    loaded.value = true
  }

  return { conversations, bound, courseId, current, loaded, load }
}
