<script setup lang="ts">
// 後端課程還沒有圖片欄位，沒有圖片時顯示鋼琴鍵盤佔位圖
defineProps<{
  src: string | null
  alt: string
  position?: string
}>()
</script>

<template>
  <div class="course-image">
    <img v-if="src" :src="src" :alt="alt" :style="{ objectPosition: position }" loading="lazy" />
    <svg v-else class="course-image__placeholder" viewBox="0 0 140 60" aria-hidden="true">
      <rect x="0" y="0" width="140" height="60" rx="4" fill="#fff" stroke="#000" stroke-opacity=".25" />
      <g stroke="#000" stroke-opacity=".25">
        <line v-for="i in 6" :key="i" :x1="i * 20" y1="0" :x2="i * 20" y2="60" />
      </g>
      <g fill="#222">
        <rect v-for="x in [14, 34, 74, 94, 114]" :key="x" :x="x" y="0" width="12" height="36" rx="1.5" />
      </g>
    </svg>
  </div>
</template>

<style scoped>
.course-image {
  position: relative;
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: linear-gradient(135deg, var(--color-placeholder-from), var(--color-placeholder-to));
}

.course-image img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.course-image__placeholder {
  width: 55%;
}
</style>
