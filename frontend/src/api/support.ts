import { request } from './http'
import type { Message, SupportConversation } from '@/types/api'

// 平台管理員和老師、學生之間的對話。老師、學生各自只有一段，所有管理員共用。

// ---------- 老師、學生
export const fetchSupportConversation = () => request<SupportConversation>('/api/support/conversation')
export const fetchSupportMessages = () => request<Message[]>('/api/support/messages')
export const sendSupportMessage = (body: string, clientMessageId: string) =>
  request<Message>('/api/support/messages', { method: 'POST', body: { body, client_message_id: clientMessageId } })

// ---------- 管理員
export const fetchAdminConversations = () => request<SupportConversation[]>('/api/admin/support/conversations')
export const fetchAdminConversation = (id: string) => request<SupportConversation>(`/api/admin/support/conversations/${id}`)
export const fetchAdminMessages = (id: string) => request<Message[]>(`/api/admin/support/conversations/${id}/messages`)
export const sendAdminMessage = (id: string, body: string, clientMessageId: string) =>
  request<Message>(`/api/admin/support/conversations/${id}/messages`, {
    method: 'POST',
    body: { body, client_message_id: clientMessageId },
  })
export const openAdminConversation = (userId: string) =>
  request<SupportConversation>(`/api/admin/support/users/${userId}/conversation`, { method: 'POST' })
