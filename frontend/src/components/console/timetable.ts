// 週課表、月曆共用：一堂課要畫的內容，以及依課程風格決定的顏色
import { styleColor } from '@/utils/courseStyle'

export interface TimetableItem {
  id: string
  starts_at: string
  ends_at: string
  title: string
  subtitle?: string
  // 課程風格（古典／流行／爵士），決定顏色；老師的時段不用
  style?: string | null
  cancelled?: boolean
  // 老師的可上課時段：open 可預約、held 學生點選了等老師完成約課。畫成虛線框
  slot?: 'open' | 'held'
  // 編輯時段時可以拖動
  draggable?: boolean
  // 編輯時段時可以拉底部的把手改結束時間
  resizable?: boolean
}

export function lessonColor(item: TimetableItem) {
  return styleColor(item.style)
}

export function startOfMonth(value: Date): Date {
  return new Date(value.getFullYear(), value.getMonth(), 1)
}
