import { computed, ref } from 'vue'
import { fetchMyChangeRequests, fetchMyConversations } from '@/api/student'
import { fetchChangeRequests, fetchTeacherConversations } from '@/api/teacher'
import type { Conversation } from '@/types/api'
import type { CurrentUser } from '@/types/user'
import { CHANGE_TYPE_LABELS, formatRange } from '@/utils/format'

// 首頁右上角鈴鐺的通知。沒有另外的通知資料表，從現有的資料整理出來：
// - 老師：學生送來、還沒處理的約課／請假／調課申請，以及有未讀訊息的聊天
// - 學生：老師已經回覆的申請（同意或未同意），以及有未讀訊息的聊天（發作業的提醒也在聊天裡）
// 「看過了沒」記在這台瀏覽器（localStorage）；聊天未讀以後端的未讀數為準，讀完就不再算新的
export interface NotificationItem {
  key: string
  icon: string
  title: string
  detail: string
  at: string
  to: string
  // 聊天有未讀訊息時一直算新的，直到在聊天室讀完
  unread: boolean
}

// 學生的申請結果只列最近兩週送出的，太舊的不提醒
const RECENT_DAYS = 14

function seenStorageKey(userId: string) {
  return `melo:notifications-seen:${userId}`
}

function readSeen(userId: string): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(seenStorageKey(userId)) ?? '[]') as string[])
  } catch {
    return new Set()
  }
}

function writeSeen(userId: string, keys: Set<string>) {
  try {
    // 只留目前還在列表上的，避免越存越多
    localStorage.setItem(seenStorageKey(userId), JSON.stringify([...keys]))
  } catch {
    // 無痕視窗等情況存不了，就每次都當作新的
  }
}

function chatItem(item: Conversation, base: string, who: string): NotificationItem {
  return {
    key: `chat:${item.id}:${item.last_message_at ?? ''}`,
    icon: '💬',
    title: `${who}傳來 ${item.unread_count} 則新訊息`,
    detail: item.last_message ?? '',
    at: item.last_message_at ?? item.created_at,
    to: `${base}/chat/${item.id}`,
    unread: true,
  }
}

async function teacherItems(): Promise<NotificationItem[]> {
  const [requests, conversations] = await Promise.all([fetchChangeRequests('pending'), fetchTeacherConversations()])
  return [
    ...requests.map((item) => {
      const time =
        item.proposed_starts_at && item.proposed_ends_at
          ? formatRange(item.proposed_starts_at, item.proposed_ends_at)
          : item.session_starts_at && item.session_ends_at
            ? formatRange(item.session_starts_at, item.session_ends_at)
            : ''
      return {
        key: `request:${item.id}:${item.status}`,
        icon: '📅',
        title: `${item.student_name}送來新的${CHANGE_TYPE_LABELS[item.request_type] ?? ''}申請`,
        detail: [item.course_title, time].filter(Boolean).join('・'),
        at: item.created_at,
        to: '/teacher/schedule',
        unread: false,
      }
    }),
    ...conversations
      .filter((item) => item.unread_count > 0)
      .map((item) => chatItem(item, '/teacher', item.student_name ?? '學生')),
  ]
}

async function studentItems(): Promise<NotificationItem[]> {
  const conversations = await fetchMyConversations()
  const bound = conversations.filter((item) => item.bound)
  const lists = await Promise.all(bound.map((item) => fetchMyChangeRequests(item.course_id).catch(() => [])))
  const since = Date.now() - RECENT_DAYS * 86_400_000
  const decided = lists.flatMap((list, index) =>
    list
      .filter((item) => item.status !== 'pending' && new Date(item.created_at).getTime() >= since)
      .map((item) => ({ item, course: bound[index]! })),
  )
  return [
    ...decided.map(({ item, course }) => ({
      key: `request:${item.id}:${item.status}`,
      icon: item.status === 'approved' ? '✅' : '↩️',
      title: `${course.teacher_name ?? ''}老師${item.status === 'approved' ? '同意了' : '沒有同意'}你的${CHANGE_TYPE_LABELS[item.request_type] ?? ''}申請`,
      detail: [
        course.course_title,
        item.proposed_starts_at && item.proposed_ends_at ? formatRange(item.proposed_starts_at, item.proposed_ends_at) : '',
      ]
        .filter(Boolean)
        .join('・'),
      at: item.created_at,
      to: '/student/schedule',
      unread: false,
    })),
    ...conversations
      .filter((item) => item.unread_count > 0)
      .map((item) => chatItem(item, '/student', `${item.teacher_name ?? ''}老師`)),
  ]
}

export function useNotifications() {
  const items = ref<NotificationItem[]>([])
  const seen = ref(new Set<string>())
  // 打開面板那一刻還沒看過的，面板開著時繼續標成新的
  const highlighted = ref(new Set<string>())
  const loading = ref(false)
  const error = ref('')
  let userId = ''

  const isUnseen = (item: NotificationItem) => item.unread || !seen.value.has(item.key)
  const isNew = (item: NotificationItem) => isUnseen(item) || highlighted.value.has(item.key)
  const newCount = computed(() => items.value.filter(isUnseen).length)

  async function load(user: CurrentUser | null) {
    if (!user || (user.role !== 'teacher' && user.role !== 'student')) {
      items.value = []
      return
    }
    userId = user.id
    seen.value = readSeen(userId)
    loading.value = true
    error.value = ''
    try {
      const list = user.role === 'teacher' ? await teacherItems() : await studentItems()
      items.value = list.sort((a, b) => b.at.localeCompare(a.at))
    } catch (problem) {
      error.value = problem instanceof Error ? problem.message : '讀不到通知。'
    } finally {
      loading.value = false
    }
  }

  // 打開鈴鐺就算看過；聊天的未讀要到聊天室讀完才消失
  function markSeen() {
    if (!userId) return
    highlighted.value = new Set(items.value.filter(isUnseen).map((item) => item.key))
    seen.value = new Set(items.value.map((item) => item.key))
    writeSeen(userId, seen.value)
  }

  return { items, loading, error, newCount, isNew, load, markSeen }
}

// 「5 分鐘前」「3 天前」
export function timeAgo(value: string): string {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 60_000))
  if (minutes < 1) return '剛剛'
  if (minutes < 60) return `${minutes} 分鐘前`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} 小時前`
  return `${Math.round(hours / 24)} 天前`
}
