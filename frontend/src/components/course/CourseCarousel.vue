<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import CoursePosterCard from './CoursePosterCard.vue'
import type { CourseSummary } from '@/types/course'

defineProps<{
  title: string
  courses: CourseSummary[]
}>()

const scroller = ref<HTMLDivElement | null>(null)
const canPrev = ref(false)
const canNext = ref(false)

function updateArrows() {
  const el = scroller.value
  if (!el) return
  canPrev.value = el.scrollLeft > 8
  canNext.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 8
}

function move(direction: number) {
  const el = scroller.value
  if (!el) return
  const distance = Math.max(el.clientWidth - 48, 220)
  el.scrollBy({ left: direction * distance, behavior: 'smooth' })
}

onMounted(async () => {
  await nextTick()
  updateArrows()
  window.addEventListener('resize', updateArrows)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateArrows)
})
</script>

<template>
  <section class="row">
    <h2 class="row__title">{{ title }}</h2>
    <div class="row__frame">
      <button
        v-show="canPrev"
        type="button"
        class="row__arrow row__arrow--prev"
        aria-label="上一排課程"
        @click="move(-1)"
      >
        ‹
      </button>
      <div ref="scroller" class="row__scroller" @scroll="updateArrows">
        <CoursePosterCard v-for="course in courses" :key="course.id" :course="course" />
      </div>
      <button
        v-show="canNext"
        type="button"
        class="row__arrow row__arrow--next"
        aria-label="下一排課程"
        @click="move(1)"
      >
        ›
      </button>
    </div>
  </section>
</template>

<style scoped>
.row {
  margin-top: 28px;
  padding-inline: clamp(72px, 8vw, 140px);
}

.row__title {
  margin: 0 0 12px;
  color: #1c1c1c;
  font-size: 22px;
  font-weight: 700;
}

.row__frame {
  position: relative;
}

.row__scroller {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 8px 0 20px;
  scroll-behavior: smooth;
  scrollbar-width: none;
}

.row__scroller::-webkit-scrollbar {
  display: none;
}

.row__arrow {
  position: absolute;
  top: 8px;
  bottom: 16px;
  z-index: 2;
  width: 48px;
  border: 0;
  background: rgba(20, 20, 20, 0.55);
  color: #fff;
  font-size: 48px;
  line-height: 1;
  cursor: pointer;
}

.row__arrow:hover {
  background: rgba(20, 20, 20, 0.82);
}

.row__arrow--prev {
  left: 0;
}

.row__arrow--next {
  right: 0;
}
</style>
