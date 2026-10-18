import { imageForCourse } from '@/assets/courseImages'
import type { CourseSummary } from '@/types/course'

// 開發排版用假資料，只在 VITE_USE_MOCK_COURSES=true 時使用，不可出現在正式環境
const mockCourseRows = [
  { id: 'mock-1', title: '古典鋼琴-入門', teacherName: 'AAA老師', durationMinutes: 60, pricePerLesson: 1200, level: '入門', imageUrl: null },
  { id: 'mock-2', title: '流行鋼琴伴奏', teacherName: 'BBB老師', durationMinutes: 90, pricePerLesson: 1800, level: '初階', imageUrl: null },
  { id: 'mock-3', title: '爵士鋼琴即興', teacherName: 'CCC老師', durationMinutes: 120, pricePerLesson: 2500, level: '中階', imageUrl: null },
  { id: 'mock-4', title: '成人鋼琴速成', teacherName: 'DDD老師', durationMinutes: 60, pricePerLesson: 1500, level: '入門', imageUrl: null },
  { id: 'mock-5', title: '古典鋼琴-初階', teacherName: 'AAA老師', durationMinutes: 120, pricePerLesson: 3000, level: '初階', imageUrl: null },
  { id: 'mock-6', title: '古典鋼琴-初階', teacherName: 'EEE老師', durationMinutes: 120, pricePerLesson: 3000, level: '初階', imageUrl: null },
  { id: 'mock-7', title: '古典鋼琴-中階', teacherName: 'AAA老師', durationMinutes: 120, pricePerLesson: 6000, level: '中階', imageUrl: null },
  { id: 'mock-8', title: '古典鋼琴-中階', teacherName: 'EEE老師', durationMinutes: 120, pricePerLesson: 6000, level: '中階', imageUrl: null },
  { id: 'mock-9', title: '古典鋼琴-高階', teacherName: 'AAA老師', durationMinutes: 120, pricePerLesson: 9000, level: '進階', imageUrl: null },
  { id: 'mock-10', title: '古典鋼琴-高階', teacherName: 'EEE老師', durationMinutes: 120, pricePerLesson: 9000, level: '進階', imageUrl: null },
]

export const mockCourses: CourseSummary[] = mockCourseRows.map((course) => ({
  style: null,
  deliveryMode: null,
  region: null,
  timeSlots: null,
  description: null,
  teacherPhotoUrl: null,
  ...course,
  imageUrl: imageForCourse(course.title),
}))
