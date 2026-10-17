import classicalPiano from '@/assets/images/古典鋼琴.png'
import popPiano from '@/assets/images/流行鋼琴.png'
import jazzPiano from '@/assets/images/爵士鋼琴.png'

const courseImages = [
  { keyword: '古典', url: classicalPiano },
  { keyword: '流行', url: popPiano },
  { keyword: '爵士', url: jazzPiano },
]

// 依課程名稱或風格挑素材。對不上的課程維持沒有圖片。
export function imageForCourse(title: string, style?: string | null): string | null {
  const text = `${style ?? ''}${title}`
  const match = courseImages.find((item) => text.includes(item.keyword))
  return match?.url ?? null
}
