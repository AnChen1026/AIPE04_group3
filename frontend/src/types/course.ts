// 對應後端 backend/schemas/student.py 的 CourseResponse
export interface CourseResponse {
  id: string
  teacher_id: string
  title: string
  level: string | null
  style: string | null
  delivery_mode: string | null
  region: string | null
  price_per_lesson: number | null
  time_slots: string | null
  status: string
  teacher_name?: string | null
}

// 首頁卡片需要的欄位。老師名稱、時數、圖片後端目前沒有回傳，先允許為空。
export interface CourseSummary {
  id: string
  title: string
  teacherName: string | null
  durationMinutes: number | null
  pricePerLesson: number | null
  level: string | null
  style: string | null
  deliveryMode: string | null
  region: string | null
  timeSlots: string | null
  imageUrl: string | null
}
