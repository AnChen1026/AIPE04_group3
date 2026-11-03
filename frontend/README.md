# 前端（Vue 正式畫面）

依 `docs/adr/0005-vue-product-ui.md`，網站所有畫面都在這裡；後端（`backend/`）只提供 API，不再有 Jinja 測試頁。登入沿用 Session Cookie。

技術：Vite、Vue 3、TypeScript、Vue Router、Pinia。

## 啟動

需要 Node.js 22.18 以上或 24.12 以上。

```bash
cd frontend
npm install
npm run dev
```

打開 <http://localhost:3000>。要讀登入狀態和課程時，另外在專案根目錄啟動後端（`python -m backend.main`，port 8000），資料庫與 `.env` 的設定見根目錄 README。

開發伺服器會把瀏覽器的 `/backend` 轉給後端，並拿掉這個前綴。例如前端打 `/backend/api/auth/me`，後端收到的是 `/api/auth/me`。瀏覽器視為同源，Session Cookie 會自動帶上。同時跑兩份後端時，可用環境變數 `BACKEND_URL` 換後端位址，預設是 `http://127.0.0.1:8000`。WebSocket 也走這條轉址。

Google 登入也走這條轉址：本機的 `GOOGLE_REDIRECT_URI` 設成 `http://localhost:3000/backend/auth/google/callback`，Google 驗證完後端會導回 Vue 的 `/student`、`/teacher` 或 `/admin`；失敗時回 `/login?error=...`，登入頁會顯示原因。

## 指令

| 指令 | 用途 |
| --- | --- |
| `npm run dev` | 開發伺服器 |
| `npm run build` | 型別檢查並打包到 `dist/` |
| `npm run lint` | oxlint 與 ESLint |

## 現在有哪些頁面

| 網址 | 誰能看 | 做什麼 |
| --- | --- | --- |
| `/` | 所有人 | 首頁。熱門課程一排 4 門（平板 2 門、手機 1 門），右側箭頭換下一組，可依程度篩選；精選老師、學習流程、常見問題是頁面文案 |
| `/courses` | 所有人 | 全部課程。一次列出所有已發布課程，可用關鍵字、風格、程度、上課方式、地區、每堂價格篩選並排序；條件記在網址上 |
| `/login`、`/signup` | 所有人 | 登入、學生註冊、老師註冊 |
| `/forgot-password` | 所有人 | 忘記密碼（地端版本）：送出 Email 後由管理員在後台重設成臨時密碼，不寄信 |
| `/courses/:id/contact` | 學生 | 從課程詳情「與老師接洽」。訪客先註冊，註冊後自動登入，建立對話並打開聊天 |
| `/teacher/...` | 老師 | 總覽、工作室、課表、學生、課程、作業、聊天、設定（個人資料、基本資料、修改密碼；舊的 `/teacher/profile` 會導到設定） |
| `/student/...` | 學生 | 資訊總覽、課表、老師（輸入綁定碼）、課程、作業（演奏作業錄音、作業分析）、聊天、設定 |
| `/admin/...` | 管理員 | 總覽、老師申請審核、老師名單、學生名單、重設密碼 |
| `/search`、`/courses/:id` | 所有人 | 還沒做，顯示開發中 |

老師、學生、管理員頁面會先確認已登入，而且角色要對。沒登入會去登入頁；角色不對會回自己的首頁。老師帳號要管理員核准後才能使用後台；用 Google 註冊、還沒有申請資料的老師，會先在老師後台補填申請。

## 檔案說明

`node_modules/`、`dist/` 是工具產生的，下面不列。

| 檔案 | 做什麼 |
| --- | --- |
| `index.html` | 網站進入點。瀏覽器先打開這個檔，再載入 Vue。 |
| `package.json` | 專案用到的套件，以及 `npm run` 的指令。 |
| `package-lock.json` | 鎖定套件版本，讓每台電腦裝到同一版。要留著。 |
| `vite.config.ts` | 開發伺服器設定。`/backend` 會轉到本機後端。 |
| `tsconfig.json` | TypeScript 總設定，再交給下面兩個檔。 |
| `tsconfig.app.json` | 檢查 `src/` 裡的 Vue 與 TypeScript。 |
| `tsconfig.node.json` | 檢查 `vite.config.ts` 這種給 Node 跑的設定檔。 |
| `env.d.ts` | 告訴 TypeScript：`.vue` 檔和 `VITE_` 環境變數是合法的。 |
| `eslint.config.ts` | ESLint 的程式風格規則。 |
| `.oxlintrc.json` | oxlint 的檢查規則。`npm run lint` 會先跑它。 |
| `.editorconfig` | 存檔時用 2 個空白縮排、檔尾換行。 |
| `.gitattributes` | 讓 Git 把文字檔的換行統一成 LF。 |
| `.gitignore` | 不要上傳的檔，例如 `node_modules/`、`dist/`。 |
| `public/favicon.ico` | 瀏覽器分頁上的小圖示。 |
| `src/main.ts` | 啟動 Vue，接上路由、Pinia，和捲動出現的 `v-reveal`。 |
| `src/App.vue` | 全站外框。首頁顯示導覽列和 AI 按鈕；登入頁和後台用自己的版面。 |
| `src/router/index.ts` | 網址對應哪個頁面，並檢查登入與角色。網址帶 `#courses` 這類錨點時捲到該區塊。 |

### 呼叫後端

所有請求都從 `src/api/http.ts` 出去，網址前面加 `/backend`，並帶上登入 Cookie。

| 檔案 | 做什麼 |
| --- | --- |
| `src/api/http.ts` | 共同的 `fetch`。JSON 和 FormData 都從這裡送。 |
| `src/api/auth.ts` | 登入、登出、註冊、讀取與修改目前登入者、Google 登入網址、Google 老師補送申請。 |
| `src/api/courses.ts` | 首頁與全部課程頁讀資料庫裡的已發布課程。 |
| `src/api/teacher.ts` | 老師後台：個人資料、課程、課表、學生、作業、聊天。 |
| `src/api/student.ts` | 學生專區：聯繫老師、綁定碼、課表、練習、聊天。 |
| `src/api/admin.ts` | 管理員：審核老師申請、讀老師與學生名單。 |
| `src/stores/auth.ts` | 把目前登入者記在前端，並決定登入後要去哪個首頁。 |
| `src/types/user.ts` | 登入者的欄位形狀。 |
| `src/types/course.ts` | 首頁課程卡用的欄位形狀。 |
| `src/types/api.ts` | 老師、學生、管理員 API 的欄位形狀，名稱沿用後端的 snake_case。 |

### 頁面

| 檔案 | 做什麼 |
| --- | --- |
| `src/views/HomeView.vue` | 首頁。課程來自後端；其餘區塊用 `src/mocks/home.ts` 的文案。 |
| `src/views/CoursesView.vue` | 全部課程與篩選。 |
| `src/views/auth/LoginView.vue` | 登入。Google 驗證失敗導回時，顯示網址上的 `error`。 |
| `src/views/auth/SignupView.vue` | 註冊。可選學生或老師。 |
| `src/views/auth/ForgotPasswordView.vue` | 忘記密碼：送出重設申請給管理員。 |
| `src/views/student/ContactTeacherView.vue` | 聯繫老師，成功後進入該堂課的聊天。 |
| `src/views/student/StudentOverviewView.vue` | 學生資訊總覽：今日課程、待老師確認的申請、待處理事項。 |
| `src/views/student/StudentTeachersView.vue` | 已綁定的老師，輸入綁定碼加入課程。 |
| `src/views/student/StudentCoursesView.vue` | 洽詢過的課程資訊（進行中／待確認）。 |
| `src/views/student/StudentHomeworkView.vue` | 作業狀態：老師發給自己的每份作業有沒有繳交。 |
| `src/views/student/StudentAssignmentView.vue` | 一份作業：下載參考 MIDI 與教材、錄音繳交、看每次回饋。 |
| `src/views/student/StudentSupportView.vue` | 和平台管理員的對話。 |
| `src/views/student/StudentAnalysisView.vue` | 作業分析入口：演奏作業；題庫作業尚未開放。 |
| `src/views/student/StudentChatListView.vue` | 學生的聊天頁：左邊對話列表，右邊是選到的對話（子路由），換人不用返回。 |
| `src/views/student/StudentChatRoomView.vue` | 學生聊天室（聊天頁右欄）。 |
| `src/views/student/StudentScheduleView.vue` | 學生課表（日／週／月切換）與約課／請假／調課申請。 |
| `src/views/student/StudentSettingsView.vue` | 學生設定：個人資料維護、修改密碼兩個分頁。 |
| `src/views/student/StudentProfileView.vue` | 學生個人資料（用 `AccountProfileForm`）。 |
| `src/views/teacher/TeacherDashboardView.vue` | 老師資訊總覽。 |
| `src/views/teacher/TeacherStudioView.vue` | 工作室資料：老師自己建立與修改，編號由系統產生。 |
| `src/views/teacher/TeacherSettingsView.vue` | 老師設定的外框：個人資料／基本資料／修改密碼三個分頁。 |
| `src/views/teacher/TeacherProfileView.vue` | 設定 → 個人資料：學生看到的老師介紹。 |
| `src/views/teacher/TeacherProfileEditView.vue` | 修改老師個人資料。姓名唯讀，在基本資料修改。 |
| `src/views/teacher/TeacherAccountView.vue` | 設定 → 基本資料：姓名、性別、手機、生日（Email 不能改）。 |
| `src/views/teacher/TeacherPasswordView.vue` | 設定 → 修改密碼。只用 Google 註冊的帳號不用輸入目前密碼。 |
| `src/components/console/AccountProfileForm.vue` | 學生與老師共用的基本資料表單。 |
| `src/views/teacher/TeacherScheduleView.vue` | 老師課表（日／週／月切換）與課務申請。 |
| `src/views/teacher/TeacherStudentsView.vue` | 各課程學生人數與已綁定的學生。 |
| `src/views/teacher/TeacherCoursesView.vue` | 老師的課程列表，每門已發布的課可以產生限時綁定碼、替洽詢中的學生發碼。 |
| `src/views/teacher/TeacherCourseFormView.vue` | 新增或修改課程，可上傳圖片和 MIDI。 |
| `src/views/teacher/TeacherPracticeView.vue` | 作業狀態：發出的每份作業有沒有繳交。 |
| `src/views/teacher/TeacherAssignmentFormView.vue` | 作業上傳：選課程、學生、期限，附參考 MIDI 與教材（演奏／題庫兩個分頁）。 |
| `src/views/teacher/TeacherAssignmentDetailView.vue` | 學生作業詳情：檔案、繳交紀錄與回饋、刪除作業。 |
| `src/views/teacher/TeacherSupportView.vue` | 和平台管理員的對話。 |
| `src/views/teacher/TeacherChatListView.vue` | 老師的聊天頁：左邊對話列表，右邊是選到的對話（子路由）。 |
| `src/views/teacher/TeacherChatRoomView.vue` | 老師聊天室（聊天頁右欄）。 |
| `src/views/admin/AdminDashboardView.vue` | 管理員資訊總覽。 |
| `src/views/admin/AdminApplicationsView.vue` | 核准或駁回老師申請。 |
| `src/views/admin/AdminPeopleView.vue` | 老師名單和學生名單共用這一頁。 |
| `src/views/admin/AdminChatListView.vue` | 管理員的聊天頁：左邊和所有老師、學生的對話，右邊是選到的對話。 |
| `src/views/admin/AdminChatRoomView.vue` | 管理員回覆一段對話。 |
| `src/views/admin/AdminPasswordResetsView.vue` | 處理忘記密碼申請：重設成臨時密碼（只顯示一次）或略過。 |
| `src/views/ComingSoonView.vue` | 搜尋、課程詳情和找不到的網址共用這一頁。 |
| `src/layouts/TeacherLayout.vue` | 老師後台的側邊選單。沒有申請資料時顯示補填表單，審核中或駁回時只顯示狀態。 |
| `src/layouts/StudentLayout.vue` | 學生專區的側邊選單。 |
| `src/layouts/AdminLayout.vue` | 管理員後台的側邊選單。 |

### 共用元件

| 檔案 | 做什麼 |
| --- | --- |
| `src/components/home/` | 首頁區塊：導覽列、主視覺、精選老師、熱門課程、關於我們、學習流程、常見問題、頁尾、課程卡、課程詳情視窗。課程卡與詳情視窗也給全部課程頁用。導覽列在有主視覺的首頁先透明，其他頁直接用米色底；區塊連結從其他頁會回首頁對應位置。 |
| `src/components/auth/AuthCard.vue` | 登入和註冊頁的外框。 |
| `src/components/auth/RolePicker.vue` | 選擇學生或老師。 |
| `src/components/console/ConsoleShell.vue` | 老師、學生、管理員後台共用的側邊選單外框。 |
| `src/components/console/ChatPanel.vue` | 聊天內容。老師和學生共用。 |
| `src/components/console/AudioRecorder.vue` | 練習錄音。沒有麥克風時可改選音檔。有給速度時附節拍器，開著錄音會帶節拍器速度。 |
| `src/components/console/DayStrip.vue` | 課表上方的星期一～日選擇列。 |
| `src/components/console/ScoreCompare.vue` | 練習回饋的上下對照樂譜（答案一行、學生一行），用 OpenSheetMusicDisplay 顯示後端產生的 MusicXML。 |
| `src/components/console/SupportChat.vue` | 平台管理員對話的聊天畫面（每 5 秒更新）。 |
| `src/components/console/CalendarPager.vue` | 課表右上方：切換日／週／月、上一段／下一段、今天。 |
| `src/components/console/WeekTimetable.vue` | 週課表格子：左邊時間、上面星期，課堂畫成色塊。 |
| `src/components/console/MonthCalendar.vue` | 月曆：一格一天，列出那天的課。 |
| `src/components/console/ChatSplit.vue` | 聊天頁的左右兩欄（老師、學生、管理員共用）。 |
| `src/components/console/CourseJoinCodes.vue` | 課程卡上的綁定碼：限時綁定碼與洽詢中學生的一人一碼。 |
| `src/components/console/CoursePicker.vue` | 學生在課表、練習頁切換已綁定的課程。 |
| `src/components/console/ImagePicker.vue` | 選擇要上傳的圖片。 |
| `src/components/console/FeedbackView.vue` | 顯示練習回饋。 |
| `src/components/console/ModalPanel.vue` | 後台共用的彈出視窗。 |
| `src/components/console/NoticeDialog.vue` | 提示或確認視窗。 |
| `src/components/console/PageHeader.vue` | 後台頁面標題。 |
| `src/components/console/ConsoleIcon.vue` | 側邊選單圖示。 |
| `src/components/console/TeacherApplicationForm.vue` | Google 註冊的老師補填教學科目、經歷、自我介紹與證明文件。 |
| `src/components/common/AiAssistButton.vue` | 右下角「AI 找課」。已接正式推薦 API，最多追問兩題並顯示已發布課程。 |
| `src/composables/useMetronome.ts` | 錄音頁的節拍器（Web Audio 排程，每小節第一拍較高）。 |
| `src/composables/useConversation.ts` | 聊天：先用 API 讀舊訊息，再用 WebSocket 收新訊息。 |
| `src/composables/useBoundCourses.ts` | 學生已綁定的課程。課表和練習用網址上的 `?course=` 記住目前選的課。 |
| `src/composables/useLeaveGuard.ts` | 表單還沒存就離開時，先問要不要放棄。 |
| `src/directives/reveal.ts` | `v-reveal`。元素捲進畫面時輕輕出現。 |
| `src/utils/format.ts` | 把日期、時間和後端代碼轉成畫面上的中文。 |
| `src/utils/redirect.ts` | 登入後要回去的網址。只接受這個角色能進的站內路徑。 |
| `src/utils/courseCard.ts` | 把後端課程轉成課程卡欄位，首頁與全部課程頁共用。 |

### 樣式、圖片、文案

| 檔案 | 做什麼 |
| --- | --- |
| `src/assets/styles/main.css` | 全站顏色、字級和首頁樣式。 |
| `src/assets/styles/console.css` | 登入頁和後台樣式。 |
| `src/assets/courseImages.ts` | 課程沒有上傳圖片時，依名稱或風格改用古典、流行、爵士三張預設圖。 |
| `src/assets/images/` | 三張課程預設圖，以及首頁精選老師用的人物圖。 |
| `src/mocks/home.ts` | 首頁文案：精選老師、學習流程、常見問題。這些還沒接後端。 |

`src/components/layout/AppHeader.vue`、`src/components/course/CourseCarousel.vue`、`CoursePosterCard.vue`、`CourseImage.vue` 是上一版橫向課程卡，現在沒有頁面引用。目前首頁用的是 `src/components/home/`。

## 課程資料從哪來

前端不會直接連 PostgreSQL，一律透過後端 API 讀資料庫。

首頁和全部課程頁呼叫 `GET /api/courses`。這支不用登入，只回資料庫裡狀態是 `published` 的課程，並帶老師姓名。草稿和封存不會出現。課程有上傳圖片就用那張；沒有就用 `src/assets/images/` 的三張預設圖。全部課程頁的風格、地區選項是從這些課程整理出來的。

## 設計稿

Figma `p6y0aWMsKEwy4ApzcWAuxF`。首頁、全部課程、登入註冊、老師後台、學生專區、管理員後台已有畫面。獨立課程詳情頁尚未完成；AI 找課推薦已接正式 FastAPI 與資料庫。
