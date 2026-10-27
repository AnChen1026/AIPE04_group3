// 週課表、月曆共用：一堂課要畫的內容，以及依課程決定的顏色

export interface TimetableItem {
  id: string
  starts_at: string
  ends_at: string
  title: string
  subtitle?: string
  colorKey: string
  cancelled?: boolean
}

// 暖色系的課程顏色，和首頁的米白、木色同一組
const PALETTE = [
  { bg: '#efe2cf', ink: '#6f5238' },
  { bg: '#e3e6d6', ink: '#55623f' },
  { bg: '#f5dfd2', ink: '#8a4f37' },
  { bg: '#e8dceb', ink: '#5f4a68' },
  { bg: '#dbe6e6', ink: '#3f5c5c' },
]

export function lessonColor(key: string) {
  let hash = 0
  for (const char of key) hash = (hash * 31 + char.charCodeAt(0)) >>> 0
  return PALETTE[hash % PALETTE.length]!
}

export function startOfMonth(value: Date): Date {
  return new Date(value.getFullYear(), value.getMonth(), 1)
}
