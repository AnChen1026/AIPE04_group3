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
  description: string | null
  image_url: string | null
}

export interface CourseInput {
  title: string
  level: string | null
  style: string | null
  delivery_mode: string | null
  region: string | null
  price_per_lesson: number | null
  time_slots: string | null
  description: string | null
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
  binding_code?: string | null
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
  // 繳交的是哪一份作業；直接照課程參考曲練習的是 null
  assignment_id: string | null
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

// 只有姓名、性別必填，其他都可以留空
export interface TeacherProfile {
  id: string
  user_id: string
  name: string
  gender: string
  age: number | null
  seniority: number | null
  expertise: string | null
  short_intros: string | null
  teaching_city: string | null
  teaching_district: string | null
  target_learning: string | null
  teaching_method: string | null
  teaching_style: string | null
  status: string
  photo_url: string | null
}

export type TeacherProfileInput = Omit<TeacherProfile, 'id' | 'user_id' | 'status' | 'photo_url'>

export interface BoundStudent {
  id: string
  email: string
  name: string
  phone_number: string | null
  courses: { course_id: string; course_title: string; bound_at: string }[]
}

export interface AssignmentMaterial {
  id: string
  filename: string
  content_type: string | null
  file_size_bytes: number
  created_at: string
}

// 老師發給一位學生的作業。performance＝演奏作業（錄音繳交），quiz＝題庫作業
export interface Assignment {
  id: string
  course_id: string
  course_title: string
  student_id: string
  student_name: string
  kind: 'performance' | 'quiz'
  title: string
  description: string | null
  due_at: string | null
  has_midi: boolean
  midi_filename: string | null
  materials: AssignmentMaterial[]
  submission_count: number
  last_submitted_at: string | null
  created_at: string
}

// 平台管理員和一位老師或學生的對話
export interface SupportConversation {
  id: string
  user_id: string
  user_name: string
  user_role: string
  created_at: string
  unread_count: number
  last_message: string | null
  last_message_at: string | null
}

export interface CourseJoinCode {
  code: string
  expires_at: string
}

export interface Studio {
  id: string
  code: string
  name: string
  owner_name: string
  city: string | null
  district: string | null
  intro: string | null
  created_at: string
  updated_at: string
}

export type StudioInput = Pick<Studio, 'name' | 'owner_name' | 'city' | 'district' | 'intro'>
