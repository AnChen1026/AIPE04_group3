// 對應後端 backend/schemas 的回傳格式。欄位名稱維持後端的 snake_case。

export interface Course {
  id: string
  teacher_id: string
  title: string
  level: string | null
  style: string | null
  delivery_mode: string | null
  region: string | null
  price_per_lesson: number | null
  time_slots: string | null
  status: 'draft' | 'published' | 'archived'
  has_reference_midi: boolean
}

export interface CourseInput {
  title: string
  level: string | null
  style: string | null
  delivery_mode: string | null
  region: string | null
  price_per_lesson: number | null
  time_slots: string | null
  status: Course['status']
}

export interface Conversation {
  id: string
  course_id: string
  teacher_id: string
  student_id: string
  created_at: string
  course_title: string | null
  course_style: string | null
  course_level: string | null
  teacher_name: string | null
  student_name: string | null
  bound: boolean | null
  unread_count: number
  last_message: string | null
  last_message_at: string | null
}

export interface Message {
  id: string
  sender_id: string
  body: string
  created_at: string
  read_at: string | null
  client_message_id: string | null
}

export interface Lesson {
  id: string
  course_id: string
  starts_at: string
  ends_at: string
  status: 'scheduled' | 'cancelled'
}

export interface TeacherLesson extends Lesson {
  student_id: string
  student_name: string
  course_title: string
}

export type ChangeRequestType = 'booking' | 'leave' | 'reschedule'

export interface ChangeRequest {
  id: string
  course_id: string
  request_type: ChangeRequestType
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  session_id: string | null
  proposed_starts_at: string | null
  proposed_ends_at: string | null
  reason: string | null
}

export interface TeacherChangeRequest extends ChangeRequest {
  student_id: string
  student_name: string
  course_title: string
  session_starts_at: string | null
  session_ends_at: string | null
}

export interface Feedback {
  pitch_score: number | null
  rhythm_score: number | null
  feedback_text: string | null
  status: 'pending' | 'completed' | 'failed'
}

export interface Recording {
  id: string
  course_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  submitted_at: string
  feedback: Feedback | null
}

export interface TeacherRecording extends Recording {
  student_id: string
  student_name: string
}

export interface LessonSummary {
  lesson_id: string
  course_id: string
  student_id: string
  lesson_starts_at: string
  window_start: string | null
  window_end: string
  summary_text: string
  written_by: 'llm' | 'rules'
  stats: {
    recording_count: number
    completed_count: number
    failed_count: number
    waiting_count: number
    average_pitch_score?: number
    average_rhythm_score?: number
  }
  source_recording_ids: string[]
  generated_at: string
}

export interface TeacherProfile {
  id: string
  user_id: string
  name: string
  gender: string
  age: number
  seniority: number
  expertise: string
  short_intros: string
  teaching_city: string
  teaching_district: string
  target_learning: string
  teaching_method: string
  teaching_style: string
  status: string
}

export type TeacherProfileInput = Omit<TeacherProfile, 'id' | 'user_id' | 'status'>

export interface BoundStudent {
  id: string
  email: string
  name: string
  phone_number: string | null
  courses: { course_id: string; course_title: string; bound_at: string }[]
}
