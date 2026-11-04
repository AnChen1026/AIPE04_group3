import { request } from './http'
import type { RecommendationCourse } from '@/types/recommendation'

export interface CourseChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface CourseChatResponse {
  reply: string
  // 回覆裡提到的課程，資料直接來自資料庫
  courses: RecommendationCourse[]
}

export const sendCourseChat = (messages: CourseChatMessage[]) =>
  request<CourseChatResponse>('/api/course-chat', { method: 'POST', body: { messages } })
