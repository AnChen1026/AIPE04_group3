import { onBeforeUnmount, ref } from 'vue'
import { API_BASE } from '@/api/http'
import type { Message } from '@/types/api'

interface ConversationApi {
  load: (id: string) => Promise<Message[]>
  send: (id: string, body: string, clientMessageId: string) => Promise<Message>
  // 目前登入者，用來判斷收到的是不是對方的訊息
  myId: () => string
}

// 一段接洽對話：先用 API 讀歷史訊息，再接 WebSocket 收新訊息。
// 送出時有連線就走 WebSocket，沒有就改用 API；同一個 client_message_id 後端只會存一次。
export function useConversation(api: ConversationApi) {
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const error = ref('')
  const connected = ref(false)
  let socket: WebSocket | null = null
  let conversationId = ''
  let retryTimer = 0
  let closedByUs = false
  let readTimer = 0

  function addMessage(message: Message) {
    if (messages.value.some((item) => item.id === message.id)) return
    const index = message.client_message_id
      ? messages.value.findIndex((item) => item.client_message_id === message.client_message_id)
      : -1
    if (index >= 0) messages.value.splice(index, 1, message)
    else messages.value.push(message)
    messages.value.sort((a, b) => a.created_at.localeCompare(b.created_at))
  }

  async function reload() {
    messages.value = await api.load(conversationId)
  }

  async function open(id: string) {
    close()
    conversationId = id
    closedByUs = false
    loading.value = true
    error.value = ''
    try {
      await reload()
    } catch (problem) {
      error.value = problem instanceof Error ? problem.message : '讀不到這段對話。'
    } finally {
      loading.value = false
    }
    connect()
  }

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    socket = new WebSocket(`${protocol}://${window.location.host}${API_BASE}/ws/conversations/${conversationId}`)
    socket.onopen = () => {
      connected.value = true
      const last = messages.value.at(-1)
      // 斷線期間可能漏了訊息，連上後補抓
      if (last) socket?.send(JSON.stringify({ type: 'sync', after_message_id: last.id }))
    }
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type !== 'message') return
      addMessage(data as Message)
      // 正在看這段對話時收到對方的新訊息，重新讀一次讓它標成已讀
      if (data.sender_id !== api.myId()) {
        window.clearTimeout(readTimer)
        readTimer = window.setTimeout(() => reload().catch(() => undefined), 800)
      }
    }
    socket.onclose = () => {
      connected.value = false
      socket = null
      if (!closedByUs) retryTimer = window.setTimeout(connect, 3000)
    }
  }

  function close() {
    closedByUs = true
    window.clearTimeout(retryTimer)
    window.clearTimeout(readTimer)
    socket?.close()
    socket = null
    connected.value = false
  }

  async function send(body: string, senderId: string) {
    const text = body.trim()
    if (!text) return
    const clientMessageId = crypto.randomUUID()
    // 先顯示在畫面上，收到伺服器的版本再換掉
    addMessage({
      id: `local-${clientMessageId}`,
      sender_id: senderId,
      body: text,
      created_at: new Date().toISOString(),
      read_at: null,
      client_message_id: clientMessageId,
    })
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'message', body: text, client_message_id: clientMessageId }))
      return
    }
    addMessage(await api.send(conversationId, text, clientMessageId))
  }

  onBeforeUnmount(close)

  return { messages, loading, error, connected, open, reload, send }
}
