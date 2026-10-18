import { request } from './http'
import type {
  BoundStudent,
  Conversation,
  Course,
  CourseInput,
  LessonSummary,
  Message,
  TeacherChangeRequest,
  TeacherLesson,
  TeacherProfile,
  TeacherProfileInput,
  TeacherRecording,
} from '@/types/api'

// ---------- 個人資料
export const fetchTeacherProfile = () => request<TeacherProfile>('/teacher/me')
export const saveTeacherProfile = (input: TeacherProfileInput) =>
  request<TeacherProfile>('/teacher/profile', { method: 'POST', body: { ...input } })

// ---------- 課程
export const fetchMyCourses = () => request<Course[]>('/teacher/courses')
export const fetchCourse = (id: string) => request<Course>(`/courses/${id}`)
export const createCourse = (input: CourseInput) => request<Course>('/courses', { method: 'POST', body: { ...input } })
export const updateCourse = (id: string, input: Partial<CourseInput>) =>
  request<Course>(`/courses/${id}`, { method: 'PATCH', body: { ...input } })

export function uploadReferenceMidi(id: string, file: File) {
  const form = new FormData()
  form.append('midi', file)
  return request<Course>(`/courses/${id}/reference-midi`, { method: 'POST', body: form })
}

// ---------- 學生
export const fetchMyStudents = () => request<BoundStudent[]>('/teacher/students')
export const unbindStudent = (courseId: string, studentId: string) =>
  request(`/teacher/courses/${courseId}/students/${studentId}/unbind`, { method: 'POST' })

// ---------- 課表與課務申請
export const fetchMyLessons = () => request<TeacherLesson[]>('/teacher/lessons')
export const fetchLessonSummary = (lessonId: string) => request<LessonSummary>(`/teacher/lessons/${lessonId}/summary`)
export const fetchChangeRequests = (status: 'pending' | 'all' = 'pending') =>
  request<TeacherChangeRequest[]>('/teacher/change-requests', { query: { status } })
export const decideChangeRequest = (id: string, approve: boolean) =>
  request<{ id: string; status: string }>(`/teacher/change-requests/${id}/decision`, { method: 'POST', body: { approve } })

// ---------- 練習錄音
export const fetchCourseRecordings = (courseId: string) =>
  request<TeacherRecording[]>(`/teacher/courses/${courseId}/recordings`)

// ---------- 聊天
export const fetchTeacherConversations = () => request<Conversation[]>('/teacher/conversations')
export const fetchTeacherConversation = (id: string) => request<Conversation>(`/teacher/conversations/${id}`)
export const fetchTeacherMessages = (id: string) => request<Message[]>(`/teacher/conversations/${id}/messages`)
export const sendTeacherMessage = (id: string, body: string, clientMessageId: string) =>
  request<Message>(`/teacher/conversations/${id}/messages`, {
    method: 'POST',
    body: { body, client_message_id: clientMessageId },
  })
export const issueBindingCode = (id: string) =>
  request<{ code: string }>(`/teacher/conversations/${id}/binding-code`, { method: 'POST' })
