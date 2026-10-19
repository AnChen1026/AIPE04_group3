<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import CourseCard from './CourseCard.vue'
import SectionHeading from './SectionHeading.vue'
import ArrowButton from './ArrowButton.vue'
import { courseLevels, type CourseCardData, type CourseLevel } from '@/mocks/home'

const props = defineProps<{
  courses: CourseCardData[]
  status?: string
}>()

const emit = defineEmits<{
  viewCourse: [course: CourseCardData]
}>()

// 首頁只放一排，一次 4 門（平板 2 門、手機 1 門），按右側箭頭換下一組；要看全部到 /courses
const perPage = ref(4)
const page = ref(0)
const direction = ref<'next' | 'prev'>('next')

const tablet = window.matchMedia('(max-width: 980px)')
const phone = window.matchMedia('(max-width: 640px)')

function updatePerPage() {
  perPage.value = phone.matches ? 1 : tablet.matches ? 2 : 4
}

onMounted(() => {
  updatePerPage()
  tablet.addEventListener('change', updatePerPage)
  phone.addEventListener('change', updatePerPage)
})

onBeforeUnmount(() => {
  tablet.removeEventListener('change', updatePerPage)
  phone.removeEventListener('change', updatePerPage)
})

const level = ref<CourseLevel | null>(null)

const matchedCourses = computed(() =>
  level.value ? props.courses.filter((course) => course.level === level.value) : props.courses,
)
const pageCount = computed(() => Math.max(1, Math.ceil(matchedCourses.value.length / perPage.value)))
const shownCourses = computed(() =>
  matchedCourses.value.slice(page.value * perPage.value, (page.value + 1) * perPage.value),
)

// 換篩選、搜尋或畫面寬度時回到第一組
watch([matchedCourses, perPage], () => {
  page.value = 0
})

// 到最後一組再按下一組就回到第一組
function next() {
  direction.value = 'next'
  page.value = (page.value + 1) % pageCount.value
}

function prev() {
  direction.value = 'prev'
  page.value = (page.value - 1 + pageCount.value) % pageCount.value
}
</script>

<template>
  <section id="courses" class="courses" aria-labelledby="courses-title">
    <div class="courses__top">
      <SectionHeading
        v-reveal
        label="熱門課程"
        title="找一門"
        accent="剛好適合你的課"
        heading-id="courses-title"
      >
        依自己的程度挑選。不確定程度也沒關係，先和老師聊聊。
      </SectionHeading>

      <div v-reveal="120" class="courses__tools">
        <div class="courses__levels" role="group" aria-label="依程度篩選">
          <button type="button" :aria-pressed="level === null" @click="level = null">全部</button>
          <button
            v-for="item in courseLevels"
            :key="item"
            type="button"
            :aria-pressed="level === item"
            @click="level = item"
          >
            {{ item }}
          </button>
        </div>
        <ArrowButton :to="{ name: 'courses' }" variant="outline">看更多</ArrowButton>
      </div>
    </div>

    <p v-if="status" class="courses__empty">{{ status }}</p>
    <p v-else-if="shownCourses.length === 0" class="courses__empty">目前沒有符合的課程，換個條件看看。</p>
    <div v-else v-reveal="160" class="courses__row">
      <div class="courses__viewport">
        <Transition :name="`courses-slide-${direction}`" mode="out-in">
          <div :key="`${level}-${page}-${perPage}`" class="courses__grid" :style="{ '--per-page': perPage }">
            <CourseCard
              v-for="course in shownCourses"
              :key="course.id"
              :course="course"
              @view-course="emit('viewCourse', $event)"
            />
          </div>
        </Transition>
      </div>
      <div v-if="pageCount > 1" class="courses__pager">
        <button type="button" class="courses__arrow courses__arrow--next" aria-label="下一組課程" @click="next">
          <svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true">
            <path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <span class="courses__count" aria-live="polite">{{ page + 1 }} / {{ pageCount }}</span>
        <button type="button" class="courses__arrow" aria-label="上一組課程" @click="prev">
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
            <path d="M10 3 5 8l5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.courses {
  width: min(1160px, calc(100% - 48px));
  margin: 0 auto;
  padding: var(--section-space) 0;
}

.courses__top {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.courses__tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 16px;
}

.courses__levels {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.courses__levels button {
  padding: 8px 18px;
  border: 1px solid var(--home-wood);
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--home-ink);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.courses__levels button:hover {
  border-color: var(--home-accent);
}

.courses__levels button[aria-pressed='true'] {
  border-color: var(--home-accent);
  background: var(--home-accent);
  color: var(--home-paper);
}

.courses__row {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 48px;
}

.courses__viewport {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.courses__grid {
  display: grid;
  grid-template-columns: repeat(var(--per-page), minmax(0, 1fr));
  gap: 24px;
}

.courses__pager {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.courses__arrow {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--home-wood);
  border-radius: 50%;
  background: transparent;
  color: var(--home-accent);
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.courses__arrow:hover {
  border-color: var(--home-accent);
}

.courses__arrow--next {
  width: 56px;
  height: 56px;
  border-color: var(--home-accent);
  background: var(--home-accent);
  color: var(--home-paper);
}

.courses__arrow--next:hover {
  background: var(--home-accent-dark);
}

.courses__count {
  color: var(--home-muted);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.courses__empty {
  margin-top: 40px;
  color: var(--home-muted);
}

.courses-slide-next-enter-active,
.courses-slide-next-leave-active,
.courses-slide-prev-enter-active,
.courses-slide-prev-leave-active {
  transition: opacity 0.28s ease, transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.courses-slide-next-enter-from,
.courses-slide-prev-leave-to {
  opacity: 0;
  transform: translateX(40px);
}

.courses-slide-next-leave-to,
.courses-slide-prev-enter-from {
  opacity: 0;
  transform: translateX(-40px);
}

@media (max-width: 640px) {
  .courses {
    width: calc(100% - 32px);
  }

  .courses__row {
    gap: 12px;
  }

  .courses__arrow--next {
    width: 44px;
    height: 44px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .courses-slide-next-enter-active,
  .courses-slide-next-leave-active,
  .courses-slide-prev-enter-active,
  .courses-slide-prev-leave-active {
    transition: none;
  }
}
</style>
