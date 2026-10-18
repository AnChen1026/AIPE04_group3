<script setup lang="ts">
import { computed, ref } from 'vue'
import HeroSection from '@/components/home/HeroSection.vue'
import FeaturedTeachers from '@/components/home/FeaturedTeachers.vue'
import PopularCourses from '@/components/home/PopularCourses.vue'
import AboutSection from '@/components/home/AboutSection.vue'
import LearningFlow from '@/components/home/LearningFlow.vue'
import FaqSection from '@/components/home/FaqSection.vue'
import JoinCta from '@/components/home/JoinCta.vue'
import Footer from '@/components/home/Footer.vue'
import {
  aboutPhotos,
  courses,
  faqs,
  highlights,
  studentSteps,
  teacherSteps,
  teachers,
} from '@/mocks/home'

const keyword = ref('')
const notice = ref('')

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
  if (!text) return courses
  return courses.filter((course) =>
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

function showCourse(title: string) {
  keyword.value = title
  notice.value = `正在看「${title}」。課程詳情頁還沒有做好。`
  document.getElementById('courses')?.scrollIntoView({ behavior: 'smooth' })
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
    <PopularCourses :courses="visibleCourses" @view-course="showCourse" />
    <LearningFlow :student-steps="studentSteps" :teacher-steps="teacherSteps" />
    <FeaturedTeachers :teachers="visibleTeachers" @view-courses="showTeacherCourses" />
    <FaqSection :faqs="faqs" />
    <JoinCta />
    <Footer />
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
