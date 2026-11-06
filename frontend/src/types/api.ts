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

// 老師開放的可上課時段。學生只看得到還沒被預約的時間
export interface AvailabilitySlot {
  id: string
  starts_at: string
  ends_at: string
}

// open：可預約；held：學生點選了、等老師完成約課；booked：已排進正式課表
export type AvailabilityStatus = 'open' | 'held' | 'booked'

export interface TeacherAvailabilitySlot extends AvailabilitySlot {
  status: AvailabilityStatus
  student_id: string | null
  student_name: string | null
  course_id: string | null
  course_title: string | null
  lesson_id: string | null
  change_request_id: string | null
}

// 每週的一段時間。weekday 0 是週一；分鐘是當天的第幾分鐘，例如 18:00 是 1080
export interface WeeklyWindow {
  weekday: number
  start_minute: number
  end_minute: number
}

export interface RecurringLesson extends WeeklyWindow {
  id: string
  student_id: string
  student_name: string
  course_id: string
  course_title: string
  future_lessons: { id: string; starts_at: string; ends_at: string }[]
}

export interface RecurringSkippedWeek {
  starts_at: string
  ends_at: string
  reason: string
}

export interface RecurringLessonResult {
  rule: RecurringLesson
  created: number
  skipped: RecurringSkippedWeek[]
}

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
  // 有答案與學生上下對照的樂譜
  has_score_sheet: boolean
}

export interface Recording {
  id: string
  course_id: string
  // 繳交的是哪一份作業；直接照課程參考曲練習的是 null
  assignment_id: string | null
  // 錄音時開的節拍器速度；沒開是 null
  metronome_bpm: number | null
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
  }
  source_recording_ids: string[]
  generated_at: string
}

// 老師的個人資料頁：帳號資料（姓名、性別、手機、生日）和介紹在一起，照片以外都必填。
// gender 是學生看到的性別（由帳號性別換算）；age 是舊資料，畫面不再填。profile_complete 沒填完不能建立課程
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
  profile_complete: boolean
  email: string | null
  sex: 'male' | 'female' | null
  phone_number: string | null
  birthdate: string | null
}

export interface TeacherProfileInput {
  name: string
  sex: 'male' | 'female'
  phone_number: string
  birthdate: string
  seniority: number
  expertise: string
  short_intros: string
  teaching_city: string
  teaching_district: string
  target_learning: string
  teaching_method: string
  teaching_style: string
}

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
  // 參考 MIDI 的速度，以及老師指定的練習速度（學生的節拍器預設用練習速度）
  midi_bpm: number | null
  practice_bpm: number | null
  teacher_name: string
  materials: AssignmentMaterial[]
  // 題庫作業有幾題
  question_count: number
  // 演奏作業是錄音繳交次數，題庫作業是作答次數
  submission_count: number
  last_submitted_at: string | null
  created_at: string
}

// 題庫作業的題型：單選、多選、是非
export type QuizQuestionType = 'single' | 'multiple' | 'truefalse'
export type QuizDifficulty = 'easy' | 'medium' | 'hard' | 'mixed'

// AI 出題預覽、老師確認後要存的一題
export interface QuizDraftQuestion {
  type: QuizQuestionType
  difficulty: QuizDifficulty | null
  topic: string | null
  question: string
  options: string[]
  answers: number[]
  hint: string | null
  explanation: string | null
}

// 一次 AI 出題（背景執行）：排隊中 → 出題中 → 待審查（succeeded）或失敗；發成作業後就不再列出
export interface QuizJob {
  id: string
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'published' | 'discarded'
  title: string | null
  course_id: string | null
  student_id: string | null
  due_at: string | null
  settings: { count: number; types: QuizQuestionType[]; difficulty: QuizDifficulty }
  source_filename: string
  provider: string | null
  model: string | null
  progress: number
  error: string | null
  created_at: string
  finished_at: string | null
  // 只有讀單筆、而且出題完成時才有
  questions: QuizDraftQuestion[] | null
}

// 學生作答時看到的一題（沒有答案）；老師看到的多了 answers 與 explanation
export interface QuizQuestion {
  id: string
  position: number
  question_type: QuizQuestionType
  difficulty: QuizDifficulty | null
  topic: string | null
  question: string
  options: string[]
  hint: string | null
  answers?: number[]
  explanation?: string | null
}

export interface QuizWrongAnswer {
  question_id: string
  position: number
  question_type: QuizQuestionType
  topic: string | null
  question: string
  options: string[]
  selected: number[]
  answers: number[]
  explanation: string | null
}

// 一次題庫作答：不給分數，只列答錯的題目
export interface QuizAttempt {
  id: string
  attempt_no: number
  submitted_at: string
  question_count: number
  wrong: QuizWrongAnswer[]
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

// 學生看老師資料頁。年齡、帳號資料不給學生
export interface StudentTeacherProfile {
  teacher_id: string
  name: string
  gender: string | null
  seniority: number | null
  expertise: string | null
  short_intros: string | null
  teaching_city: string | null
  teaching_district: string | null
  target_learning: string | null
  teaching_method: string | null
  teaching_style: string | null
  photo_url: string | null
  course_styles: string[]
  courses: { course_id: string; course_title: string | null; course_style: string | null; conversation_id: string; bound: boolean }[]
}
