<script setup lang="ts">
import { computed, ref } from 'vue'
import HeroSection from '@/components/home/HeroSection.vue'
import FeaturedTeachers from '@/components/home/FeaturedTeachers.vue'
import PopularCourses from '@/components/home/PopularCourses.vue'
import Footer from '@/components/home/Footer.vue'
import { courses, teachers } from '@/mocks/home'

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
    [course.title, course.category, course.teacherName].some((field) => field.toLowerCase().includes(text)),
  )
})

function showTeacherCourses(teacherName: string) {
  keyword.value = teacherName
  notice.value = `正在看 ${teacherName} 的課程。`
  document.getElementById('courses')?.scrollIntoView({ behavior: 'smooth' })
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
    <p v-if="notice" class="home__notice">{{ notice }}</p>
    <FeaturedTeachers :teachers="visibleTeachers" @view-courses="showTeacherCourses" />
    <PopularCourses :courses="visibleCourses" @view-course="showCourse" />
    <Footer />
  </div>
</template>

<style scoped>
.home {
  background: var(--home-bg);
  color: var(--home-ink);
}

.home__notice {
  width: min(1120px, calc(100% - 48px));
  margin: 28px auto 0;
  color: var(--home-muted);
}

@media (max-width: 640px) {
  .home__notice {
    width: calc(100% - 32px);
  }
}
</style>
