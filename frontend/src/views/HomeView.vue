<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import HeroSection from '@/components/home/HeroSection.vue'
import FeaturedTeachers from '@/components/home/FeaturedTeachers.vue'
import PopularCourses from '@/components/home/PopularCourses.vue'
import AboutSection from '@/components/home/AboutSection.vue'
import LearningFlow from '@/components/home/LearningFlow.vue'
import FaqSection from '@/components/home/FaqSection.vue'
import JoinCta from '@/components/home/JoinCta.vue'
import Footer from '@/components/home/Footer.vue'
import CourseDetailDialog from '@/components/home/CourseDetailDialog.vue'
import { fetchPublishedCourses } from '@/api/courses'
import type { CourseSummary } from '@/types/course'
import {
  aboutPhotos,
  faqs,
  highlights,
  studentSteps,
  teacherSteps,
  teachers,
  type CourseCardData,
} from '@/mocks/home'

const keyword = ref('')
const notice = ref('')
const courses = ref<CourseCardData[]>([])
const courseStatus = ref('正在讀取已發布的課程…')
const selectedCourse = ref<CourseCardData | null>(null)

function deliveryLabel(mode: string | null): string {
  if (mode === 'online' || mode === '線上') return '線上'
  if (mode === 'in_person' || mode === '實體') return '實體'
  return '未填'
}

function toCourseCard(course: CourseSummary): CourseCardData {
  const summary =
    course.description || [course.region, course.timeSlots].filter((item): item is string => Boolean(item)).join(' · ')
  return {
    id: course.id,
    title: course.title,
    category: course.style || '鋼琴課',
    teacherName: course.teacherName || '未填老師',
    cover: course.imageUrl,
    level: course.level || '未填',
    format: deliveryLabel(course.deliveryMode),
    minutes: course.durationMinutes,
    price: course.pricePerLesson,
    summary,
    region: course.region,
    timeSlots: course.timeSlots,
    description: course.description,
    teacherPhoto: course.teacherPhotoUrl,
  }
}

onMounted(async () => {
  try {
    courses.value = (await fetchPublishedCourses()).map(toCourseCard)
    courseStatus.value = ''
  } catch (problem) {
    courseStatus.value = problem instanceof Error ? problem.message : '讀不到課程，請確認後端有啟動。'
  }
})

const query = computed(() => keyword.value.trim().toLowerCase())

const visibleTeachers = computed(() => {
  const text = query.value
  if (!text) return teachers
  return teachers.filter((teacher) =>
    [teacher.name, teacher.specialty, teacher.bio].some((field) => field.toLowerCase().includes(text)),
  )
})

const visibleCourses = computed(() => {
  const text = query.value
  if (!text) return courses.value
  return courses.value.filter((course) =>
    [course.title, course.category, course.teacherName, course.level].some((field) => field.toLowerCase().includes(text)),
  )
})

function showTeacherCourses(teacherName: string) {
  keyword.value = teacherName
  notice.value = `正在看 ${teacherName} 的課程。`
  document.getElementById('courses')?.scrollIntoView({ behavior: 'smooth' })
}

function clearSearch() {
  keyword.value = ''
  notice.value = ''
}

// 點課程卡打開課程詳情，裡面有「與老師接洽」
function showCourse(course: CourseCardData) {
  selectedCourse.value = course
}
</script>

<template>
  <div class="home">
    <HeroSection v-model="keyword" />
    <AboutSection :photos="aboutPhotos" :highlights="highlights" />
    <p v-if="notice" class="home__notice">
      {{ notice }}
      <button type="button" @click="clearSearch">看全部課程</button>
    </p>
    <PopularCourses :courses="visibleCourses" :status="courseStatus" @view-course="showCourse" />
    <LearningFlow :student-steps="studentSteps" :teacher-steps="teacherSteps" />
    <FeaturedTeachers :teachers="visibleTeachers" @view-courses="showTeacherCourses" />
    <FaqSection :faqs="faqs" />
    <JoinCta />
    <Footer />
    <CourseDetailDialog :course="selectedCourse" @close="selectedCourse = null" />
  </div>
</template>

<style scoped>
.home {
  background: var(--home-bg);
  color: var(--home-ink);
}

.home__notice {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  width: min(1160px, calc(100% - 48px));
  margin: 64px auto -48px;
  padding: 14px 20px;
  border-radius: var(--radius-pill);
  background: var(--home-cream);
  color: var(--home-ink);
  font-size: 15px;
}

.home__notice button {
  border: 0;
  border-bottom: 1px solid var(--home-accent);
  background: transparent;
  color: var(--home-accent);
  cursor: pointer;
}

@media (max-width: 640px) {
  .home__notice {
    width: calc(100% - 32px);
  }
}
</style>
