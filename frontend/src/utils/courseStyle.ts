// 課程風格固定三選一，每種風格一個固定顏色。課表（日／週／月）、課程卡片、學生管理都用這一份，
// 同一門課在哪裡看都是同一個顏色。色碼還在等 UIUX 確認，之後只要改這裡
export const COURSE_STYLES = ['古典', '流行', '爵士'] as const
export type CourseStyle = (typeof COURSE_STYLES)[number]

// 課程表單的選項。存進資料庫的值沿用既有資料的「古典鋼琴」寫法，首頁搜尋、推薦都不用改
export const COURSE_STYLE_OPTIONS: { value: string; label: CourseStyle }[] = COURSE_STYLES.map((label) => ({
  value: `${label}鋼琴`,
  label,
}))

// 課程的可上課時段改成勾選（可複選），存成「平日晚上、週末下午」這樣的文字
export const TIME_SLOT_OPTIONS = ['平日上午', '平日下午', '平日晚上', '週末上午', '週末下午', '週末晚上'] as const

// 舊資料是自由打字的，只留下對得上選項的部分
export function parseTimeSlots(value: string | null | undefined): string[] {
  const parts = (value ?? '').split(/[、,，\s]+/)
  return TIME_SLOT_OPTIONS.filter((option) => parts.includes(option))
}

export interface StyleColor {
  // 卡片底色、文字色、按鈕色、框線色
  bg: string
  ink: string
  strong: string
  line: string
}

// 避開「可預約」的綠色虛線和「待完成約課」的橘色虛線
const COLORS: Record<CourseStyle, StyleColor> = {
  古典: { bg: '#dbe5fa', ink: '#1f5aa6', strong: '#7fa8e6', line: '#9dbbe9' },
  流行: { bg: '#fbe1e8', ink: '#b03a62', strong: '#ef9bb5', line: '#f0b3c6' },
  爵士: { bg: '#e9def5', ink: '#6a3f9e', strong: '#b99ae0', line: '#c9b2e6' },
}

// 舊資料的風格不是這三種時（老師以前可以自由打字）用中性色
const OTHER: StyleColor = { bg: '#efe8df', ink: '#6f5238', strong: '#d9c4a8', line: '#dccbb5' }

// 「古典鋼琴」「古典」都算古典；都對不上時是 null
export function styleKind(style: string | null | undefined): CourseStyle | null {
  return COURSE_STYLES.find((name) => style?.includes(name)) ?? null
}

// 表單用：舊資料轉成三個選項之一的值，對不上就留空讓老師重選
export function styleOptionValue(style: string | null | undefined): string {
  const kind = styleKind(style)
  return kind ? `${kind}鋼琴` : ''
}

export function styleColor(style: string | null | undefined): StyleColor {
  const kind = styleKind(style)
  return kind ? COLORS[kind] : OTHER
}

// 給 .tone-card 用：把風格的顏色放進卡片的 CSS 變數
export function styleToneVars(style: string | null | undefined): Record<string, string> {
  const color = styleColor(style)
  return {
    '--tone-bg': color.bg,
    '--tone-ink': color.ink,
    '--tone-strong': color.strong,
    '--tone-line': color.line,
  }
}
