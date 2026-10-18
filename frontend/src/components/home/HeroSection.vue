<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import coverImage from '@/assets/images/封面大圖.png'

const keyword = defineModel<string>({ default: '' })

const heroRef = ref<HTMLElement | null>(null)
const stageRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)

const reduced = ref(window.matchMedia('(prefers-reduced-motion: reduce)').matches)
const progress = ref(0)
const introScale = ref(reduced.value ? 1 : 1.08)

const stageStyle = computed(() => {
  if (reduced.value) return undefined
  const zoom = introScale.value * (1 + progress.value * 0.18)
  const shift = progress.value * -6
  return { transform: `scale(${zoom}) translate3d(0, ${shift}%, 0)` }
})

function scrollToTeachers() {
  document.getElementById('teachers')?.scrollIntoView({ behavior: 'smooth' })
}

function updateProgress() {
  const hero = heroRef.value
  if (!hero || reduced.value) return
  const distance = hero.offsetHeight - window.innerHeight
  const passed = Math.min(Math.max(-hero.getBoundingClientRect().top, 0), distance)
  progress.value = distance > 0 ? passed / distance : 0
}

type Point = { x: number; y: number }
type Ripple = { x: number; y: number; born: number }

let frameId = 0
let introId = 0
let pointerOnHero = false
let hasPointer = false
const target: Point = { x: 0, y: 0 }
const current: Point = { x: 0, y: 0 }
const trail: Point[] = []
const ripples: Ripple[] = []
const lensCanvas = document.createElement('canvas')
let mediaQuery: MediaQueryList | null = null

function localPoint(event: PointerEvent): Point {
  const canvas = canvasRef.value
  if (!canvas) return { x: 0, y: 0 }
  const rect = canvas.getBoundingClientRect()
  const scaleX = rect.width ? canvas.clientWidth / rect.width : 1
  const scaleY = rect.height ? canvas.clientHeight / rect.height : 1
  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY,
  }
}

function onPointerMove(event: PointerEvent) {
  if (reduced.value) return
  const point = localPoint(event)
  const previous = trail[trail.length - 1]
  target.x = point.x
  target.y = point.y
  if (!hasPointer) {
    current.x = point.x
    current.y = point.y
    hasPointer = true
  }
  if (!previous || Math.hypot(point.x - previous.x, point.y - previous.y) > 28) {
    ripples.push({ x: point.x, y: point.y, born: performance.now() })
    if (ripples.length > 5) ripples.shift()
  }
  pointerOnHero = true
  startWater()
}

function onPointerLeave() {
  pointerOnHero = false
}

function resizeCanvas() {
  const canvas = canvasRef.value
  const stage = stageRef.value
  if (!canvas || !stage) return
  const ratio = Math.min(window.devicePixelRatio || 1, 1.5)
  const width = stage.clientWidth
  const height = stage.clientHeight
  canvas.width = Math.max(1, Math.round(width * ratio))
  canvas.height = Math.max(1, Math.round(height * ratio))
}

function drawCover(
  context: CanvasRenderingContext2D,
  boxWidth: number,
  boxHeight: number,
  zoom: number,
  originX: number,
  originY: number,
) {
  const image = imageRef.value
  if (!image?.naturalWidth) return
  const base = Math.max(boxWidth / image.naturalWidth, boxHeight / image.naturalHeight)
  const drawnWidth = image.naturalWidth * base
  const drawnHeight = image.naturalHeight * base
  const restX = (boxWidth - drawnWidth) * 0.5
  const restY = (boxHeight - drawnHeight) * 0.62
  context.drawImage(
    image,
    originX - (originX - restX) * zoom,
    originY - (originY - restY) * zoom,
    drawnWidth * zoom,
    drawnHeight * zoom,
  )
}

function paintLens(
  main: CanvasRenderingContext2D,
  point: Point,
  radius: number,
  alpha: number,
) {
  const size = 480
  if (lensCanvas.width !== size) {
    lensCanvas.width = size
    lensCanvas.height = size
  }
  const lens = lensCanvas.getContext('2d')
  if (!lens) return
  const boxWidth = canvasRef.value?.clientWidth ?? 1
  const boxHeight = canvasRef.value?.clientHeight ?? 1

  lens.setTransform(1, 0, 0, 1, 0, 0)
  lens.clearRect(0, 0, size, size)
  lens.save()
  lens.scale(size / (radius * 2), size / (radius * 2))
  lens.translate(radius - point.x, radius - point.y)
  drawCover(lens, boxWidth, boxHeight, 1.42, point.x, point.y)
  lens.restore()

  lens.globalCompositeOperation = 'destination-in'
  const mask = lens.createRadialGradient(size / 2, size / 2, size * 0.08, size / 2, size / 2, size / 2)
  mask.addColorStop(0, 'rgba(0, 0, 0, 1)')
  mask.addColorStop(0.62, 'rgba(0, 0, 0, 0.8)')
  mask.addColorStop(1, 'rgba(0, 0, 0, 0)')
  lens.fillStyle = mask
  lens.fillRect(0, 0, size, size)

  lens.globalCompositeOperation = 'source-over'
  const light = lens.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
  light.addColorStop(0, 'rgba(255, 252, 245, 0.78)')
  light.addColorStop(0.28, 'rgba(255, 255, 255, 0.38)')
  light.addColorStop(0.7, 'rgba(255, 248, 236, 0.12)')
  light.addColorStop(1, 'rgba(255, 255, 255, 0)')
  lens.fillStyle = light
  lens.fillRect(0, 0, size, size)

  main.save()
  main.globalAlpha = alpha
  main.drawImage(lensCanvas, point.x - radius, point.y - radius, radius * 2, radius * 2)
  main.restore()
}

function drawWater(now: number) {
  const canvas = canvasRef.value
  const context = canvas?.getContext('2d')
  if (!canvas || !context) return

  const ratio = canvas.width / canvas.clientWidth
  context.setTransform(ratio, 0, 0, ratio, 0, 0)
  context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight)
  if (!hasPointer) return

  current.x += (target.x - current.x) * 0.18
  current.y += (target.y - current.y) * 0.18
  trail.push({ x: current.x, y: current.y })
  if (trail.length > 8) trail.shift()

  const radius = Math.min(canvas.clientWidth, canvas.clientHeight) * 0.34
  trail.forEach((point, index) => {
    const strength = (index + 1) / trail.length
    paintLens(context, point, radius * (0.55 + strength * 0.45), 0.22 + strength * 0.78)
  })

  ripples.forEach((ripple) => {
    const age = (now - ripple.born) / 1200
    if (age >= 1) return
    context.beginPath()
    context.arc(ripple.x, ripple.y, 30 + age * 180, 0, Math.PI * 2)
    context.strokeStyle = `rgba(255, 250, 242, ${(1 - age) * 0.7})`
    context.lineWidth = 2
    context.stroke()
  })
  for (let index = ripples.length - 1; index >= 0; index -= 1) {
    if (now - ripples[index].born > 1200) ripples.splice(index, 1)
  }
}

function startWater() {
  if (frameId || reduced.value) return
  const loop = (now: number) => {
    drawWater(now)
    const settled = Math.hypot(target.x - current.x, target.y - current.y) < 0.4
    if (!pointerOnHero && settled && ripples.length === 0) {
      const canvas = canvasRef.value
      const context = canvas?.getContext('2d')
      if (canvas && context) {
        context.setTransform(1, 0, 0, 1, 0, 0)
        context.clearRect(0, 0, canvas.width, canvas.height)
      }
      frameId = 0
      trail.length = 0
      return
    }
    frameId = requestAnimationFrame(loop)
  }
  frameId = requestAnimationFrame(loop)
}

function runIntro() {
  const started = performance.now()
  const step = (now: number) => {
    const amount = Math.min(1, (now - started) / 1600)
    const eased = 1 - (1 - amount) ** 3
    introScale.value = 1.08 - eased * 0.08
    if (amount < 1) introId = requestAnimationFrame(step)
  }
  introId = requestAnimationFrame(step)
}

function onMotionChange(event: MediaQueryListEvent) {
  reduced.value = event.matches
  if (reduced.value) {
    progress.value = 0
    introScale.value = 1
  }
}

onMounted(() => {
  resizeCanvas()
  updateProgress()
  window.addEventListener('scroll', updateProgress, { passive: true })
  window.addEventListener('resize', resizeCanvas)
  window.addEventListener('resize', updateProgress)
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  mediaQuery.addEventListener('change', onMotionChange)
  if (!reduced.value) runIntro()
})

onUnmounted(() => {
  window.removeEventListener('scroll', updateProgress)
  window.removeEventListener('resize', resizeCanvas)
  window.removeEventListener('resize', updateProgress)
  mediaQuery?.removeEventListener('change', onMotionChange)
  cancelAnimationFrame(frameId)
  cancelAnimationFrame(introId)
})
</script>

<template>
  <section
    ref="heroRef"
    class="hero"
    :class="{ 'hero--motion': !reduced }"
    aria-labelledby="hero-title"
  >
    <div class="hero__pin">
      <div
        ref="stageRef"
        class="hero__stage"
        :style="stageStyle"
        @pointermove="onPointerMove"
        @pointerleave="onPointerLeave"
      >
        <img
          ref="imageRef"
          class="hero__image"
          :src="coverImage"
          alt="夕陽草地與一架打開琴蓋的鋼琴"
        />
        <canvas ref="canvasRef" class="hero__water" aria-hidden="true"></canvas>
        <div class="hero__scrim"></div>
        <div class="hero__copy">
          <h1 id="hero-title">找一位老師，把想彈的曲子練完。</h1>
          <p>古典、流行、爵士都可以。先從適合自己的步調開始。</p>
          <form class="hero__search" role="search" @submit.prevent="scrollToTeachers">
            <label class="visually-hidden" for="home-search">搜尋老師或課程</label>
            <input
              id="home-search"
              v-model="keyword"
              type="search"
              placeholder="搜尋老師或課程"
            />
            <button type="submit">搜尋</button>
          </form>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero--motion {
  height: 200dvh;
}

.hero__pin {
  position: sticky;
  top: 0;
  height: 100dvh;
  overflow: hidden;
}

.hero__stage {
  position: relative;
  height: 100%;
  transform-origin: center 58%;
  will-change: transform;
}

.hero__image,
.hero__water {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.hero__image {
  max-width: none;
  object-fit: cover;
  object-position: center 62%;
}

.hero__water {
  z-index: 2;
  pointer-events: none;
}

.hero__scrim {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(180deg, rgba(62, 52, 44, 0.05) 20%, rgba(62, 52, 44, 0.46));
  pointer-events: none;
}

.hero__copy {
  position: absolute;
  z-index: 3;
  right: clamp(20px, 4vw, 48px);
  bottom: clamp(28px, 5vh, 56px);
  left: clamp(20px, 4vw, 48px);
  max-width: 640px;
  color: #fffaf3;
  opacity: 0;
  animation: hero-fade 0.8s ease 0.25s forwards;
}

.hero__copy h1 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: clamp(32px, 4vw, 52px);
  font-weight: 600;
  line-height: 1.2;
}

.hero__copy p {
  margin: 12px 0 0;
  font-size: 18px;
}

.hero__search {
  display: flex;
  gap: 8px;
  max-width: 460px;
  margin-top: 22px;
  padding: 6px 6px 6px 18px;
  border-radius: var(--radius-pill);
  background: var(--home-paper);
}

.hero__search input {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  color: var(--home-ink);
  outline: none;
}

.hero__search button {
  border: 0;
  border-radius: var(--radius-pill);
  padding: 10px 18px;
  background: var(--home-accent);
  color: var(--home-paper);
  cursor: pointer;
}

.hero__search button:hover {
  background: var(--home-accent-dark);
}

@keyframes hero-fade {
  to {
    opacity: 1;
  }
}

@media (max-width: 640px) {
  .hero--motion {
    height: 150dvh;
  }

  .hero__copy p {
    font-size: 16px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero__copy {
    animation: none;
    opacity: 1;
  }

  .hero__water {
    display: none;
  }
}
</style>
