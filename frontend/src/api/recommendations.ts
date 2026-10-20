import { request } from './http'
import type { RecommendationResponse } from '@/types/recommendation'

export const startRecommendation = (message: string) =>
  request<RecommendationResponse>('/api/recommendations', { method: 'POST', body: { message } })

export const answerRecommendation = (sessionId: string, message: string) =>
  request<RecommendationResponse>(`/api/recommendations/${sessionId}/answer`, {
    method: 'POST',
    body: { message },
  })

export const fetchRecommendation = (sessionId: string) =>
  request<RecommendationResponse>(`/api/recommendations/${sessionId}`)
