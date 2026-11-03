export type RecommendationStatus = 'asking' | 'done' | 'unsupported'

export interface RecommendationCourse {
  id: string
  title: string
  teacher_name: string
  level: string | null
  style: string | null
  delivery_mode: string | null
  region: string | null
  price_per_lesson: number | null
  time_slots: string | null
  description: string | null
  image_url: string | null
  teacher_photo_url: string | null
}

export interface RecommendationItem {
  course: RecommendationCourse
  matched: string[]
  unknown: string[]
  reason: string
}

export interface RecommendationResponse {
  session_id: string
  status: RecommendationStatus
  question: string | null
  questions_asked: number
  criteria: Record<string, string | number | null>
  message: string
  results: RecommendationItem[]
}
