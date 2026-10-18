import classicalCover from '@/assets/images/古典鋼琴.png'
import popCover from '@/assets/images/流行鋼琴.png'
import jazzCover from '@/assets/images/爵士鋼琴.png'
import teacherLin from '@/assets/images/女老師1.png'
import teacherChen from '@/assets/images/男老師1.png'
import teacherChou from '@/assets/images/女老師2.png'
import teacherKao from '@/assets/images/男老師2.png'
import studioFemale from '@/assets/images/女老師3.png'
import studioMale from '@/assets/images/男老師3.png'

// 找課程度只有這幾種，和 GLOSSARY 的「找課程度」一致
export type CourseLevel = '入門' | '初階' | '中階' | '進階'

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
  level: CourseLevel
  format: '線上' | '實體'
  minutes: number
  price: number
  summary: string
}

export interface HighlightItem {
  title: string
  text: string
}

export interface FlowStep {
  title: string
  tag: string
  text: string
}

export interface FaqItem {
  question: string
  answer: string
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

export const courseLevels: CourseLevel[] = ['入門', '初階', '中階', '進階']

export const courses: CourseCardData[] = [
  {
    id: 'course-classical',
    title: '古典鋼琴入門',
    category: '古典鋼琴',
    teacherName: '林安柔',
    cover: classicalCover,
    level: '入門',
    format: '實體',
    minutes: 60,
    price: 1200,
    summary: '從坐姿、手型和讀譜開始，三個月內彈完第一首小奏鳴曲。',
  },
  {
    id: 'course-pop',
    title: '流行鋼琴伴奏',
    category: '流行鋼琴',
    teacherName: '周以恩',
    cover: popCover,
    level: '初階',
    format: '線上',
    minutes: 50,
    price: 1000,
    summary: '學會常用和弦與伴奏型，把喜歡的歌改成自己能彈的版本。',
  },
  {
    id: 'course-jazz',
    title: '爵士鋼琴即興',
    category: '爵士鋼琴',
    teacherName: '陳子謙',
    cover: jazzCover,
    level: '中階',
    format: '實體',
    minutes: 60,
    price: 1500,
    summary: '練藍調音階和七和弦，在固定的和弦進行裡試著說出自己的句子。',
  },
]

export const aboutPhotos = [
  { src: studioFemale, alt: '老師在琴房裡示範' },
  { src: classicalCover, alt: '陽光下的平台鋼琴' },
  { src: studioMale, alt: '老師坐在鋼琴前' },
]

// 下面的文字依照 PRD 與 User Flow 的流程撰寫
export const highlights: HighlightItem[] = [
  {
    title: '只推薦真的有開的課',
    text: '推薦只會出現老師已發布的鋼琴課。找不到合適的，就直接告訴你，不會編一門課出來。',
  },
  {
    title: '先聊聊，再決定',
    text: '在課程上按「洽詢」就能和老師對話，不用填申請表。確定要上課，老師再給你綁定碼。',
  },
  {
    title: '每一次練習都有回饋',
    text: '照老師指定的曲子錄音，音高和節奏分開呈現，還有針對這一次的文字說明。',
  },
]

export const studentSteps: FlowStep[] = [
  { title: '說說想學什麼', tag: '免登入', text: '用自己的話描述，最多再回答兩個問題，就會從已發布的課程中幫你挑選。' },
  { title: '洽詢老師', tag: '需登入', text: '在喜歡的課程按洽詢，直接開始和老師的對話。可以同時問好幾門課。' },
  { title: '輸入綁定碼', tag: '老師提供', text: '老師決定收你之後，會把只屬於你的綁定碼貼在對話裡，輸入後就進入這門課。' },
  { title: '排課、請假、調課', tag: '綁定後', text: '在課表上提出申請，老師同意、而且時段空著之後，正式課表才會改動。' },
  { title: '錄音，看這一次的回饋', tag: '綁定後', text: '沒有麥克風也能上傳音檔。每一筆錄音都有自己的音高、節奏與文字說明。' },
]

export const teacherSteps: FlowStep[] = [
  { title: '發布課程', tag: '老師', text: '填寫程度、風格、線上或實體、地區、價格與時段。發布後才會出現在推薦裡。' },
  { title: '回覆洽詢', tag: '老師', text: '和學生聊聊需求，決定收這位學生時，把綁定碼貼進同一段對話。' },
  { title: '指定練習曲', tag: '每門課一份', text: '為課程設定一份參考 MIDI，學生的練習回饋都會以這首曲子為準。' },
  { title: '上課前看摘要', tag: '課前', text: '整理這位學生從上一堂結束到這一堂之前的練習。沒有紀錄時也會如實說明。' },
  { title: '用教材出測驗', tag: 'AI 協助', text: '提供教材讓 AI 產生題目草稿，檢查修改後再發布給學生作答。' },
]

export const faqs: FaqItem[] = [
  {
    question: '不登入也能找課嗎？',
    answer: '可以。描述想學的內容就能看到推薦，想洽詢老師時再註冊或登入即可。',
  },
  {
    question: '綁定碼是什麼？',
    answer: '老師發給你一個人、只對應一門課的上課資格。輸入後才會開啟這門課的課表和練習，不能轉給別人使用。',
  },
  {
    question: '可以同時問好幾位老師嗎？',
    answer: '可以。每一門課各有一段對話，彼此分開，綁定之後也會沿用同一段對話。',
  },
  {
    question: '沒有麥克風怎麼錄音？',
    answer: '可以把錄好的音檔上傳，一樣會和老師指定的曲子比對。',
  },
  {
    question: '練習的分數會影響我的程度嗎？',
    answer: '不會。練習回饋只描述那一次錄音，不會改變你找課時的程度。',
  },
]
