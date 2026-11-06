<script setup lang="ts">
import { COURSE_STYLES, styleColor } from '@/utils/courseStyle'

// 週課表、月曆的圖例：三種課程風格的顏色，以及老師時段的兩種虛線框。日檢視用不到
defineProps<{ slots?: boolean }>()
</script>

<template>
  <ul class="legend" aria-label="圖例">
    <li v-for="style in COURSE_STYLES" :key="style">
      <span class="legend__swatch" :style="{ background: styleColor(style).bg, borderColor: styleColor(style).line }"></span>{{ style }}
    </li>
    <template v-if="slots">
      <li><span class="legend__swatch legend__swatch--open"></span>可預約</li>
      <li><span class="legend__swatch legend__swatch--held"></span>待完成約課</li>
    </template>
  </ul>
</template>

<style scoped>
.legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 16px;
  margin: 0;
  padding: 0;
  color: var(--home-muted);
  font-size: 13px;
  list-style: none;
}

.legend li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend__swatch {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 1.5px solid transparent;
  border-radius: 4px;
}

/* 和週課表、月曆上的時段同色 */
.legend__swatch--open,
.legend__swatch--held {
  border-style: dashed;
  border-color: currentColor;
}

.legend__swatch--open {
  background: #eef3e6;
  color: #55623f;
}

.legend__swatch--held {
  background: #fbefd9;
  color: #8a5a1f;
}
</style>
