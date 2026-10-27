import { apiUrl, request } from './http'
import type { Assignment, ChangeRequest, ChangeRequestType, Conversation, Lesson, Message, Recording } from '@/types/api'

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

// 只輸入綁定碼就加入課程
export const joinWithCode = (code: string) =>
  request<{ bound: boolean; course_id: string; conversation_id: string }>('/api/student/bind', {
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

// ---------- 作業：老師發給自己的作業、下載檔案、錄音繳交
export const fetchMyAssignments = () => request<Assignment[]>('/api/student/assignments')
export const fetchAssignmentRecordings = (id: string) => request<Recording[]>(`/api/student/assignments/${id}/recordings`)
export const studentAssignmentMidiUrl = (id: string) => apiUrl(`/api/student/assignments/${id}/midi`)
export const studentMaterialUrl = (id: string) => apiUrl(`/api/student/assignment-materials/${id}`)
export const studentScoreSheetUrl = (recordingId: string) => apiUrl(`/api/student/recordings/${recordingId}/score-sheet`)

// 錄音時有開節拍器就帶速度，節奏照節拍器評分
export function submitAssignment(id: string, audio: Blob, filename: string, metronomeBpm: number | null = null) {
  const form = new FormData()
  form.append('audio', audio, filename)
  if (metronomeBpm) form.append('metronome_bpm', String(metronomeBpm))
  return request<Recording>(`/api/student/assignments/${id}/recordings`, { method: 'POST', body: form })
}
