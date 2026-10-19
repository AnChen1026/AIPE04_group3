<script setup lang="ts">
// 後台左側選單與卡片用的線條圖示
defineProps<{ name: string; size?: number }>()

const paths: Record<string, string> = {
  overview: 'M4 13h6V4H4zm10 7h6v-9h-6zM4 20h6v-5H4zm10-11h6V4h-6z',
  studio: 'M4 20V9l8-5 8 5v11M9 20v-6h6v6',
  profile: 'M4 5h16v14H4zM8 10h3M8 14h8M15 9.5a1.5 1.5 0 1 0 0 .01',
  schedule: 'M4 6h16v14H4zM4 10h16M8 3v5M16 3v5',
  students: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M16 5.5a3 3 0 0 1 0 5.6M18 14.4c1.8.9 3 2.9 3 5.6',
  courses: 'M4 5c2.5-1 5.5-1 8 1v14c-2.5-2-5.5-2-8-1zM20 5c-2.5-1-5.5-1-8 1v14c2.5-2 5.5-2 8-1z',
  practice: 'M7 3h7l4 4v14H7zM14 3v4h4M10 12h5M10 16h5',
  chat: 'M4 5h16v11H9l-5 4zM8 10h.01M12 10h.01M16 10h.01',
  logout: 'M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10',
  home: 'M4 11 12 4l8 7v9h-5v-6H9v6H4z',
  mic: 'M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM6 11a6 6 0 0 0 12 0M12 17v4',
  calendar: 'M4 6h16v14H4zM4 10h16M8 3v5M16 3v5',
  users: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M17 8v6M14 11h6',
  clipboard: 'M8 4h8v3H8zM6 6H5v15h14V6h-1M9 12h6M9 16h4',
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM20 20l-4-4',
  back: 'M15 5l-7 7 7 7',
  send: 'M4 12 20 4l-6 16-3-7z',
  settings: 'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM12 3l1.6 2.3 2.8-.4.6 2.7 2.5 1.3-1 2.6 1 2.6-2.5 1.3-.6 2.7-2.8-.4L12 21l-1.6-2.3-2.8.4-.6-2.7-2.5-1.3 1-2.6-1-2.6 2.5-1.3.6-2.7 2.8.4z',
  music: 'M9 18V5l11-2v13M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM20 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0z',
}
</script>

<template>
  <svg
    :width="size ?? 20"
    :height="size ?? 20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="paths[name] ?? paths.overview" />
  </svg>
</template>
