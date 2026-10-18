import classicalCover from '@/assets/images/古典鋼琴.png'
import popCover from '@/assets/images/流行鋼琴.png'
import jazzCover from '@/assets/images/爵士鋼琴.png'
import teacherLin from '@/assets/images/女老師1.png'
import teacherChen from '@/assets/images/男老師1.png'
import teacherChou from '@/assets/images/女老師2.png'
import teacherKao from '@/assets/images/男老師2.png'

export interface TeacherCardData {
  id: string
  name: string
  specialty: string
  bio: string
  photo: string
}

export interface CourseCardData {
  id: string
  title: string
  category: string
  teacherName: string
  cover: string
}

// 首頁假資料。之後改接 API 時，只要換這個檔案的資料來源。
export const teachers: TeacherCardData[] = [
  {
    id: 'teacher-lin',
    name: '林安柔',
    specialty: '古典鋼琴',
    bio: '從基本手型與樂譜開始，讓初學者也能穩穩彈完一首曲子。',
    photo: teacherLin,
  },
  {
    id: 'teacher-chen',
    name: '陳子謙',
    specialty: '爵士鋼琴',
    bio: '用耳朵聽和弦，再慢慢把即興變成自己的句子。',
    photo: teacherChen,
  },
  {
    id: 'teacher-chou',
    name: '周以恩',
    specialty: '流行鋼琴',
    bio: '把喜歡的歌拆成伴奏，練到可以邊唱邊彈。',
    photo: teacherChou,
  },
  {
    id: 'teacher-kao',
    name: '高承恩',
    specialty: '古典鋼琴',
    bio: '適合已經有基礎、想把音色和樂句練得更乾淨的人。',
    photo: teacherKao,
  },
]

export const courses: CourseCardData[] = [
  {
    id: 'course-classical',
    title: '古典鋼琴入門',
    category: '古典鋼琴',
    teacherName: '林安柔',
    cover: classicalCover,
  },
  {
    id: 'course-pop',
    title: '流行鋼琴伴奏',
    category: '流行鋼琴',
    teacherName: '周以恩',
    cover: popCover,
  },
  {
    id: 'course-jazz',
    title: '爵士鋼琴即興',
    category: '爵士鋼琴',
    teacherName: '陳子謙',
    cover: jazzCover,
  },
]
