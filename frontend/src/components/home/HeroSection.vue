<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import coverImage from '@/assets/images/封面大圖.png'

const keyword = defineModel<string>({ default: '' })

const heroRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)

const reduced = ref(window.matchMedia('(prefers-reduced-motion: reduce)').matches)
// progress 是畫面上看到的進度，會慢慢追上捲軸位置，滾一格後還會再滑一小段
const progress = ref(0)
const look = ref({ x: 0, y: 0 })
const introScale = ref(reduced.value ? 1 : 1.06)

const clamp = (value: number, min = 0, max = 1) => Math.min(Math.max(value, min), max)
const easeOut = (value: number) => 1 - (1 - value) ** 3
const easeInOut = (value: number) => (value < 0.5 ? 4 * value ** 3 : 1 - (-2 * value + 2) ** 3 / 2)

// 捲動時只有圖片往前推進；滑鼠位置讓視角往反方向偏一點
const mediaStyle = computed(() => {
  if (reduced.value) return undefined
  const zoom = introScale.value * (1.05 + easeInOut(progress.value) * 0.26)
  const shiftX = look.value.x * -18
  const shiftY = look.value.y * -12
  return { transform: `translate3d(${shiftX}px, ${shiftY}px, 0) scale(${zoom})` }
})

// 文字維持原本大小，一直留到大圖快要換到下方內容時才淡出
const copyStyle = computed(() => {
  if (reduced.value) return undefined
  const fade = easeInOut(clamp((progress.value - 0.72) / 0.28))
  return {
    opacity: String(1 - fade),
    transform: `translate3d(${look.value.x * 6}px, ${fade * -32 + look.value.y * 4}px, 0)`,
    visibility: fade >= 0.99 ? ('hidden' as const) : undefined,
  }
})

const scrimStyle = computed(() => {
  if (reduced.value) return undefined
  return { opacity: String(1 - easeInOut(clamp(progress.value / 0.9)) * 0.45) }
})

function scrollToCourses() {
  document.getElementById('courses')?.scrollIntoView({ behavior: 'smooth' })
}

let targetProgress = 0
const lookTarget = { x: 0, y: 0 }

function readProgress() {
  const hero = heroRef.value
  if (!hero || reduced.value) return
  const distance = hero.offsetHeight - window.innerHeight
  const passed = clamp(-hero.getBoundingClientRect().top, 0, distance)
  targetProgress = distance > 0 ? passed / distance : 0
  startLoop()
}

// 滑鼠經過時留下一縷柔和的白色光霧，隨時間擴散、淡掉
type Puff = { x: number; y: number; vx: number; vy: number; size: number; born: number; life: number }

let frameId = 0
let introId = 0
let lastTime = 0
let last: { x: number; y: number } | null = null
const puffs: Puff[] = []
let mediaQuery: MediaQueryList | null = null

function onPointerMove(event: PointerEvent) {
  if (reduced.value || event.pointerType === 'touch') return
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  lookTarget.x = clamp((x / rect.width) * 2 - 1, -1, 1)
  lookTarget.y = clamp((y / rect.height) * 2 - 1, -1, 1)
  startLoop()

  if (!last) {
    last = { x, y }
    return
  }
  const dx = x - last.x
  const dy = y - last.y
  const distance = Math.hypot(dx, dy)
  if (distance < 6) return

  const now = performance.now()
  const steps = Math.min(4, Math.ceil(distance / 26))
  for (let step = 1; step <= steps; step += 1) {
    const t = step / steps
    puffs.push({
      x: last.x + dx * t,
      y: last.y + dy * t,
      vx: dx * 0.012 + (Math.random() - 0.5) * 0.25,
      vy: dy * 0.012 - 0.18 - Math.random() * 0.2,
      size: 26 + Math.random() * 22,
      born: now,
      life: 1300 + Math.random() * 700,
    })
  }
  if (puffs.length > 90) puffs.splice(0, puffs.length - 90)
  last = { x, y }
}

function onPointerLeave() {
  last = null
  lookTarget.x = 0
  lookTarget.y = 0
  startLoop()
}

function resizeCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ratio = Math.min(window.devicePixelRatio || 1, 1.5)
  canvas.width = Math.max(1, Math.round(canvas.clientWidth * ratio))
  canvas.height = Math.max(1, Math.round(canvas.clientHeight * ratio))
}

function drawSmoke(now: number) {
  const canvas = canvasRef.value
  const context = canvas?.getContext('2d')
  if (!canvas || !context) return

  const ratio = canvas.width / canvas.clientWidth
  context.setTransform(ratio, 0, 0, ratio, 0, 0)
  context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight)

  for (let index = puffs.length - 1; index >= 0; index -= 1) {
    const puff = puffs[index]!
    const age = (now - puff.born) / puff.life
    if (age >= 1) {
      puffs.splice(index, 1)
      continue
    }
    puff.x += puff.vx
    puff.y += puff.vy
    puff.vx *= 0.97
    puff.vy *= 0.985

    const radius = puff.size * (0.6 + easeOut(age) * 2.4)
    // 先淡入再慢慢散掉，避免一出現就是一顆亮點
    const alpha = Math.min(1, age * 6) * (1 - age) ** 1.6 * 0.13
    const glow = context.createRadialGradient(puff.x, puff.y, 0, puff.x, puff.y, radius)
    glow.addColorStop(0, `rgba(255, 249, 238, ${alpha})`)
    glow.addColorStop(0.45, `rgba(255, 246, 232, ${alpha * 0.5})`)
    glow.addColorStop(1, 'rgba(255, 246, 232, 0)')
    context.fillStyle = glow
    context.beginPath()
    context.arc(puff.x, puff.y, radius, 0, Math.PI * 2)
    context.fill()
  }
}

// 每一幀只追上剩下距離的一小部分，停下滾輪後還會順勢滑一段才停
function approach(current: number, target: number, rate: number, frames: number) {
  return current + (target - current) * (1 - (1 - rate) ** frames)
}

function startLoop() {
  if (frameId || reduced.value) return
  lastTime = performance.now()
  const loop = (now: number) => {
    const frames = Math.min(4, (now - lastTime) / (1000 / 60))
    lastTime = now

    progress.value = approach(progress.value, targetProgress, 0.07, frames)
    look.value = {
      x: approach(look.value.x, lookTarget.x, 0.05, frames),
      y: approach(look.value.y, lookTarget.y, 0.05, frames),
    }
    drawSmoke(now)

    const settled =
      Math.abs(targetProgress - progress.value) < 0.0005 &&
      Math.abs(lookTarget.x - look.value.x) < 0.002 &&
      Math.abs(lookTarget.y - look.value.y) < 0.002 &&
      puffs.length === 0
    if (settled) {
      progress.value = targetProgress
      frameId = 0
      return
    }
    frameId = requestAnimationFrame(loop)
  }
  frameId = requestAnimationFrame(loop)
}

function runIntro() {
  const started = performance.now()
  const step = (now: number) => {
    const amount = Math.min(1, (now - started) / 2200)
    introScale.value = 1.06 - easeOut(amount) * 0.06
    if (amount < 1) introId = requestAnimationFrame(step)
  }
  introId = requestAnimationFrame(step)
}

function onMotionChange(event: MediaQueryListEvent) {
  reduced.value = event.matches
  if (reduced.value) {
    progress.value = 0
    look.value = { x: 0, y: 0 }
    introScale.value = 1
    puffs.length = 0
  }
}

onMounted(() => {
  resizeCanvas()
  readProgress()
  progress.value = targetProgress
  window.addEventListener('scroll', readProgress, { passive: true })
  window.addEventListener('resize', resizeCanvas)
  window.addEventListener('resize', readProgress)
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  mediaQuery.addEventListener('change', onMotionChange)
  if (!reduced.value) runIntro()
})

onUnmounted(() => {
  window.removeEventListener('scroll', readProgress)
  window.removeEventListener('resize', resizeCanvas)
  window.removeEventListener('resize', readProgress)
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
    <div class="hero__pin" @pointermove="onPointerMove" @pointerleave="onPointerLeave">
      <div class="hero__media" :style="mediaStyle">
        <img class="hero__image" :src="coverImage" alt="夕陽草地與一架打開琴蓋的鋼琴" />
      </div>
      <canvas ref="canvasRef" class="hero__smoke" aria-hidden="true"></canvas>
      <div class="hero__scrim" :style="scrimStyle"></div>
      <div class="hero__copy" :style="copyStyle">
        <p class="hero__eyebrow">鋼琴課程推薦</p>
        <h1 id="hero-title">讓喜歡的音樂<em>成為生活的一部分</em></h1>
        <p class="hero__lead">古典、流行、爵士，遇見適合的老師，讓音樂陪你走得更遠</p>
        <form class="hero__search" role="search" @submit.prevent="scrollToCourses">
          <label class="visually-hidden" for="home-search">搜尋老師或課程</label>
          <input id="home-search" v-model="keyword" type="search" placeholder="搜尋老師或課程" />
          <button type="submit">搜尋</button>
        </form>
      </div>
      <p class="hero__hint" :style="copyStyle" aria-hidden="true">往下捲動</p>
    </div>
  </section>
</template>

<style scoped>
.hero--motion {
  height: 210dvh;
}

.hero__pin {
  position: sticky;
  top: 0;
  height: 100dvh;
  overflow: hidden;
  background: #e9dccb;
}

.hero__media,
.hero__smoke,
.hero__scrim {
  position: absolute;
  inset: 0;
}

.hero__media {
  /* 推進的焦點放在鋼琴附近，像鏡頭慢慢往前走 */
  transform-origin: 50% 60%;
  will-change: transform;
}

.hero__image {
  width: 100%;
  height: 100%;
  max-width: none;
  object-fit: cover;
  object-position: center 62%;
  /* 讓偏藍綠的封面圖靠近米色木質的整體色調 */
  filter: saturate(0.82) sepia(0.12) brightness(1.02);
}

.hero__smoke {
  z-index: 1;
  width: 100%;
  height: 100%;
  pointer-events: none;
  filter: blur(14px);
}

.hero__scrim {
  z-index: 2;
  background:
    linear-gradient(180deg, rgba(62, 52, 44, 0.18), rgba(62, 52, 44, 0) 22%),
    linear-gradient(180deg, rgba(62, 52, 44, 0) 40%, rgba(52, 42, 34, 0.5));
  pointer-events: none;
}

.hero__copy {
  position: absolute;
  z-index: 3;
  right: clamp(20px, 5vw, 72px);
  bottom: clamp(36px, 9vh, 96px);
  left: clamp(20px, 5vw, 72px);
  max-width: 680px;
  color: var(--home-paper);
  animation: hero-rise 1.1s cubic-bezier(0.22, 1, 0.36, 1) 0.3s both;
}

.hero__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 18px;
  padding: 6px 14px;
  border: 1px solid rgba(255, 250, 243, 0.5);
  border-radius: var(--radius-pill);
  font-size: 13px;
  letter-spacing: 0.12em;
  backdrop-filter: blur(6px);
}

.hero__eyebrow::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.hero__copy h1 {
  margin: 0;
  font-family: var(--font-sans);
  font-size: clamp(34px, 4.6vw, 64px);
  font-weight: 500;
  line-height: 1.18;
  letter-spacing: 0.02em;
  text-shadow: 0 2px 24px rgba(52, 42, 34, 0.28);
}

.hero__copy h1 em {
  display: block;
  font-family: var(--font-serif);
  font-style: normal;
  font-weight: 500;
  color: #f6e7d2;
}

.hero__lead {
  margin: 18px 0 0;
  font-size: 17px;
  line-height: 1.7;
  opacity: 0.92;
}

.hero__search {
  display: flex;
  gap: 8px;
  max-width: 480px;
  margin-top: 28px;
  padding: 6px 6px 6px 22px;
  border-radius: var(--radius-pill);
  background: var(--home-paper);
  box-shadow: 0 14px 36px rgba(52, 42, 34, 0.22);
}

.hero__search input {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  color: var(--home-ink);
  outline: none;
}

.hero__search input::placeholder {
  color: var(--home-muted);
}

.hero__search button {
  border: 0;
  border-radius: var(--radius-pill);
  padding: 11px 22px;
  background: var(--home-accent);
  color: var(--home-paper);
  cursor: pointer;
  transition: background 0.2s ease;
}

.hero__search button:hover {
  background: var(--home-accent-dark);
}

.hero__hint {
  position: absolute;
  z-index: 3;
  top: 50%;
  right: clamp(20px, 3vw, 40px);
  margin: 0;
  color: var(--home-paper);
  font-size: 12px;
  letter-spacing: 0.24em;
  writing-mode: vertical-rl;
}

.hero__hint::after {
  content: '';
  display: block;
  width: 1px;
  height: 48px;
  margin: 12px auto 0;
  background: linear-gradient(var(--home-paper), transparent);
}

@keyframes hero-rise {
  from {
    opacity: 0;
    translate: 0 18px;
  }
}

@media (max-width: 760px) {
  .hero__hint {
    display: none;
  }
}

@media (max-width: 640px) {
  .hero--motion {
    height: 170dvh;
  }

  .hero__lead {
    font-size: 15px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero__copy {
    animation: none;
  }

  .hero__smoke {
    display: none;
  }
}
</style>
