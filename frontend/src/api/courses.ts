import { apiUrl, request } from './http'
import { imageForCourse } from '@/assets/courseImages'
import { mockCourses } from '@/mocks/courses'
import type { CourseResponse, CourseSummary } from '@/types/course'

const useMock = import.meta.env.VITE_USE_MOCK_COURSES === 'true'

function toCourseSummary(course: CourseResponse): CourseSummary {
  return {
    id: course.id,
    title: course.title,
    teacherName: course.teacher_name ?? null,
    durationMinutes: null,
    pricePerLesson: course.price_per_lesson,
    level: course.level,
    style: course.style,
    deliveryMode: course.delivery_mode,
    region: course.region,
    timeSlots: course.time_slots,
    imageUrl: course.image_url ? apiUrl(course.image_url) : imageForCourse(course.title, course.style),
    description: course.description ?? null,
    teacherPhotoUrl: course.teacher_photo_url ? apiUrl(course.teacher_photo_url) : null,
  }
}

// ======================================================
// 已發布課程：首頁只能顯示資料庫裡的已發布課程，不編造課程
// ======================================================
export async function fetchPublishedCourses(): Promise<CourseSummary[]> {
  if (useMock) {
    return mockCourses
  }

  const courses = await request<CourseResponse[]>('/api/courses')
  return courses.map(toCourseSummary)
}
