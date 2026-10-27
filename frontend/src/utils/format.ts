// 畫面上的日期、標籤文字。後端存的是代碼，這裡統一轉成中文。

const WEEKDAYS = ['週日', '週一', '週二', '週三', '週四', '週五', '週六']

export function formatDate(value: string | Date | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  return `${date.getFullYear()}/${pad(date.getMonth() + 1)}/${pad(date.getDate())}（${WEEKDAYS[date.getDay()]}）`
}

export function formatTime(value: string | Date | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function formatDateTime(value: string | Date | null | undefined): string {
  if (!value) return '—'
  return `${formatDate(value)} ${formatTime(value)}`
}

export function formatRange(start: string, end: string): string {
  return `${formatDate(start)} ${formatTime(start)}－${formatTime(end)}`
}

// 聊天列表用：今天只顯示時間，其他天顯示月日
export function formatShort(value: string | null | undefined): string {
  if (!value) return ''
  const date = new Date(value)
  const today = new Date()
  if (date.toDateString() === today.toDateString()) return formatTime(date)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

export function pad(value: number): string {
  return String(value).padStart(2, '0')
}

// <input type="datetime-local"> 需要的格式
export function toLocalInput(value: Date): string {
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}`
}

export const COURSE_LEVELS = ['入門', '初階', '中階', '進階', '不確定']

export const DELIVERY_LABELS: Record<string, string> = { online: '線上', in_person: '實體', 線上: '線上', 實體: '實體' }

export const COURSE_STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  published: '已發布',
  archived: '已封存',
}

export const CHANGE_TYPE_LABELS: Record<string, string> = {
  booking: '約課',
  leave: '請假',
  reschedule: '調課',
}

export const CHANGE_STATUS_LABELS: Record<string, string> = {
  pending: '待老師確認',
  approved: '已同意',
  rejected: '未同意',
}

export const RECORDING_STATUS_LABELS: Record<string, string> = {
  pending: '等待分析',
  processing: '分析中',
  completed: '已完成',
  failed: '分析失敗',
}

export function deliveryText(value: string | null | undefined): string {
  return value ? (DELIVERY_LABELS[value] ?? value) : '未填'
}

export function priceText(value: number | null | undefined): string {
  return value === null || value === undefined ? '價格未填' : `NT$ ${value.toLocaleString('zh-TW')} / 堂`
}

export function startOfWeek(value: Date): Date {
  const date = new Date(value)
  const offset = (date.getDay() + 6) % 7 // 週一為一週的第一天
  date.setHours(0, 0, 0, 0)
  date.setDate(date.getDate() - offset)
  return date
}

export function addDays(value: Date, days: number): Date {
  const date = new Date(value)
  date.setDate(date.getDate() + days)
  return date
}

export function sameDay(a: Date, b: Date): boolean {
  return a.toDateString() === b.toDateString()
}

// 卡片三色輪流：同一門課固定同一色（依 keys 裡的順序）
export function toneClass(key: string, keys: string[]): string {
  const index = Math.max(keys.indexOf(key), 0) % 3
  return index ? `tone-card--${index}` : ''
}

// 作業的繳交期限：「繳交期限：2026-11-05 剩餘 3 天」；沒設定時是「待定」
export function dueText(value: string | null | undefined): string {
  if (!value) return '繳交期限：待定'
  const due = new Date(value)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const day = new Date(due)
  day.setHours(0, 0, 0, 0)
  const days = Math.round((day.getTime() - today.getTime()) / 86_400_000)
  const date = `${due.getFullYear()}-${pad(due.getMonth() + 1)}-${pad(due.getDate())}`
  if (days > 0) return `繳交期限：${date} 剩餘 ${days} 天`
  if (days === 0) return `繳交期限：${date}（今天）`
  return `繳交期限：${date}（已過 ${-days} 天）`
}

export const ASSIGNMENT_KIND_LABELS: Record<string, string> = { performance: '演奏作業', quiz: '題庫作業' }

export function fileSizeText(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

// 老師個人資料、工作室的縣市選單
export const TAIWAN_CITIES = [
  '台北市', '新北市', '基隆市', '桃園市', '新竹市', '新竹縣', '苗栗縣', '台中市', '彰化縣', '南投縣',
  '雲林縣', '嘉義市', '嘉義縣', '台南市', '高雄市', '屏東縣', '宜蘭縣', '花蓮縣', '台東縣', '澎湖縣', '金門縣', '連江縣',
]
