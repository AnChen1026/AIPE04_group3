import { request } from './http'
import type { ChangeRequest, ChangeRequestType, Conversation, Lesson, Message, Recording } from '@/types/api'

// ---------- 接洽對話與綁定
export const startConversation = (courseId: string) =>
  request<Conversation>(`/api/student/courses/${courseId}/conversation`, { method: 'POST' })
export const fetchMyConversations = () => request<Conversation[]>('/api/student/conversations')
export const fetchMyConversation = (id: string) => request<Conversation>(`/api/student/conversations/${id}`)
export const fetchStudentMessages = (id: string) => request<Message[]>(`/api/student/conversations/${id}/messages`)
export const sendStudentMessage = (id: string, body: string, clientMessageId: string) =>
  request<Message>(`/api/student/conversations/${id}/messages`, {
    method: 'POST',
    body: { body, client_message_id: clientMessageId },
  })
export const redeemBindingCode = (conversationId: string, code: string) =>
  request<{ bound: boolean; course_id: string }>(`/api/student/conversations/${conversationId}/bind`, {
    method: 'POST',
    body: { code },
  })

// ---------- 課表與課務申請
export const fetchStudentSchedule = (courseId: string) => request<Lesson[]>(`/api/student/courses/${courseId}/schedule`)
export const fetchMyChangeRequests = (courseId: string) =>
  request<ChangeRequest[]>(`/api/student/courses/${courseId}/change-requests`)

export interface ChangeRequestInput {
  request_type: ChangeRequestType
  session_id?: string | null
  proposed_starts_at?: string | null
  proposed_ends_at?: string | null
  reason?: string | null
}

export const createChangeRequest = (courseId: string, input: ChangeRequestInput) =>
  request<ChangeRequest>(`/api/student/courses/${courseId}/change-requests`, {
    method: 'POST',
    query: { ...input },
  })

// ---------- 練習錄音
export const fetchMyRecordings = (courseId: string) => request<Recording[]>(`/api/student/courses/${courseId}/recordings`)
export const fetchMyRecording = (id: string) => request<Recording>(`/api/student/recordings/${id}`)

export function uploadRecording(courseId: string, audio: Blob, filename: string) {
  const form = new FormData()
  form.append('audio', audio, filename)
  return request<Recording>(`/api/student/courses/${courseId}/recordings`, { method: 'POST', body: form })
}
