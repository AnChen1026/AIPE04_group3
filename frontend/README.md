# 前端（Vue 正式畫面）

依 `docs/adr/0005-vue-product-ui.md`，正式畫面用 Vue；後端 API 在根目錄 FastAPI，登入沿用 Session Cookie。

技術：Vite、Vue 3、TypeScript、Vue Router、Pinia。

## 啟動

需要 Node.js 22.18 以上或 24.12 以上。

```bash
cd frontend
npm install
npm run dev
```

打開 <http://localhost:3000>。要讀登入狀態和課程時，另外在根目錄啟動後端（`python app.py`，port 8000）。

開發伺服器會把瀏覽器的 `/backend` 轉給後端，並拿掉這個前綴。例如前端打 `/backend/api/auth/me`，後端收到的是 `/api/auth/me`。瀏覽器視為同源，Session Cookie 會自動帶上。同時跑兩份後端時，可用環境變數 `BACKEND_URL` 換後端位址，預設是 `http://127.0.0.1:8000`。WebSocket 也走這條轉址。

## 指令

| 指令 | 用途 |
| --- | --- |
| `npm run dev` | 開發伺服器 |
| `npm run build` | 型別檢查並打包到 `dist/` |
| `npm run lint` | oxlint 與 ESLint |

## 現在有哪些頁面

| 網址 | 誰能看 | 做什麼 |
| --- | --- | --- |
| `/` | 所有人 | 首頁。已發布課程來自後端；精選老師、學習流程、常見問題是頁面文案 |
| `/login`、`/signup` | 所有人 | 登入、學生註冊、老師註冊 |
| `/forgot-password` | 所有人 | 忘記密碼的版面。後端還沒有重設密碼，送出只會說明目前不能寄信 |
| `/courses/:id/contact` | 學生 | 從課程聯繫老師。未登入會先去登入，登入後建立對話並打開聊天 |
| `/teacher/...` | 老師 | 總覽、工作室、個人資料、課表、學生、課程、作業、聊天 |
| `/student/...` | 學生 | 我的課程、聊天、課表、練習、基本資料 |
| `/admin/...` | 管理員 | 總覽、老師申請審核、老師名單、學生名單 |
| `/search`、`/courses/:id` | 所有人 | 還沒做，顯示開發中 |

老師、學生、管理員頁面會先確認已登入，而且角色要對。沒登入會去登入頁；角色不對會回自己的首頁。老師帳號要管理員核准後才能使用後台。

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
| `.env.development` | 只有開發時生效。現在用它決定首頁課程要不要改看假資料。 |
| `eslint.config.ts` | ESLint 的程式風格規則。 |
| `.oxlintrc.json` | oxlint 的檢查規則。`npm run lint` 會先跑它。 |
| `.editorconfig` | 存檔時用 2 個空白縮排、檔尾換行。 |
| `.gitattributes` | 讓 Git 把文字檔的換行統一成 LF。 |
| `.gitignore` | 不要上傳的檔，例如 `node_modules/`、`dist/`。 |
| `public/favicon.ico` | 瀏覽器分頁上的小圖示。 |
| `src/main.ts` | 啟動 Vue，接上路由、Pinia，和捲動出現的 `v-reveal`。 |
| `src/App.vue` | 全站外框。首頁顯示導覽列和 AI 按鈕；登入頁和後台用自己的版面。 |
| `src/router/index.ts` | 網址對應哪個頁面，並檢查登入與角色。 |

### 呼叫後端

所有請求都從 `src/api/http.ts` 出去，網址前面加 `/backend`，並帶上登入 Cookie。

| 檔案 | 做什麼 |
| --- | --- |
| `src/api/http.ts` | 共同的 `fetch`。JSON 和 FormData 都從這裡送。 |
| `src/api/auth.ts` | 登入、登出、註冊、讀取目前登入者。 |
| `src/api/courses.ts` | 首頁讀已發布課程。開發時可改走假資料。 |
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
| `src/views/auth/LoginView.vue` | 登入。 |
| `src/views/auth/SignupView.vue` | 註冊。可選學生或老師。 |
| `src/views/auth/ForgotPasswordView.vue` | 忘記密碼版面。尚未呼叫後端。 |
| `src/views/student/ContactTeacherView.vue` | 聯繫老師，成功後進入該堂課的聊天。 |
| `src/views/student/StudentDashboardView.vue` | 學生的課程與對話。 |
| `src/views/student/StudentChatRoomView.vue` | 學生聊天室。 |
| `src/views/student/StudentScheduleView.vue` | 學生課表與調課申請。 |
| `src/views/student/StudentPracticeView.vue` | 學生練習錄音。 |
| `src/views/student/StudentProfileView.vue` | 學生基本資料。 |
| `src/views/teacher/TeacherDashboardView.vue` | 老師資訊總覽。 |
| `src/views/teacher/TeacherStudioView.vue` | 工作室管理。 |
| `src/views/teacher/TeacherProfileView.vue` | 老師個人資料。 |
| `src/views/teacher/TeacherProfileEditView.vue` | 修改老師個人資料。 |
| `src/views/teacher/TeacherScheduleView.vue` | 老師課表。 |
| `src/views/teacher/TeacherStudentsView.vue` | 已綁定的學生。 |
| `src/views/teacher/TeacherCoursesView.vue` | 老師的課程列表。 |
| `src/views/teacher/TeacherCourseFormView.vue` | 新增或修改課程，可上傳圖片和 MIDI。 |
| `src/views/teacher/TeacherPracticeView.vue` | 老師看學生作業。 |
| `src/views/teacher/TeacherChatListView.vue` | 老師的對話列表。 |
| `src/views/teacher/TeacherChatRoomView.vue` | 老師聊天室。 |
| `src/views/admin/AdminDashboardView.vue` | 管理員資訊總覽。 |
| `src/views/admin/AdminApplicationsView.vue` | 核准或駁回老師申請。 |
| `src/views/admin/AdminPeopleView.vue` | 老師名單和學生名單共用這一頁。 |
| `src/views/ComingSoonView.vue` | 搜尋、課程詳情和找不到的網址共用這一頁。 |
| `src/layouts/TeacherLayout.vue` | 老師後台的側邊選單。未核准時只顯示審核狀態。 |
| `src/layouts/StudentLayout.vue` | 學生專區的側邊選單。 |
| `src/layouts/AdminLayout.vue` | 管理員後台的側邊選單。 |

### 共用元件

| 檔案 | 做什麼 |
| --- | --- |
| `src/components/home/` | 首頁區塊：導覽列、主視覺、精選老師、熱門課程、關於我們、學習流程、常見問題、頁尾、課程詳情視窗。 |
| `src/components/auth/AuthCard.vue` | 登入和註冊頁的外框。 |
| `src/components/auth/RolePicker.vue` | 選擇學生或老師。 |
| `src/components/console/ConsoleShell.vue` | 老師、學生、管理員後台共用的側邊選單外框。 |
| `src/components/console/ChatPanel.vue` | 聊天內容。老師和學生共用。 |
| `src/components/console/AudioRecorder.vue` | 練習錄音。沒有麥克風時可改選音檔。 |
| `src/components/console/WeekTimetable.vue` | 一週課表。 |
| `src/components/console/WeekPicker.vue` | 選擇要看的那一週。 |
| `src/components/console/CoursePicker.vue` | 學生在課表、練習頁切換已綁定的課程。 |
| `src/components/console/ImagePicker.vue` | 選擇要上傳的圖片。 |
| `src/components/console/FeedbackView.vue` | 顯示練習回饋。 |
| `src/components/console/ModalPanel.vue` | 後台共用的彈出視窗。 |
| `src/components/console/NoticeDialog.vue` | 提示或確認視窗。 |
| `src/components/console/PageHeader.vue` | 後台頁面標題。 |
| `src/components/console/ConsoleIcon.vue` | 側邊選單圖示。 |
| `src/components/common/AiAssistButton.vue` | 右下角「AI 找課」。視窗還是提示文字，尚未推薦課程。 |
| `src/composables/useConversation.ts` | 聊天：先用 API 讀舊訊息，再用 WebSocket 收新訊息。 |
| `src/composables/useBoundCourses.ts` | 學生已綁定的課程。課表和練習用網址上的 `?course=` 記住目前選的課。 |
| `src/composables/useLeaveGuard.ts` | 表單還沒存就離開時，先問要不要放棄。 |
| `src/directives/reveal.ts` | `v-reveal`。元素捲進畫面時輕輕出現。 |
| `src/utils/format.ts` | 把日期、時間和後端代碼轉成畫面上的中文。 |
| `src/utils/redirect.ts` | 登入後要回去的網址。只接受這個角色能進的站內路徑。 |

### 樣式、圖片、假資料

| 檔案 | 做什麼 |
| --- | --- |
| `src/assets/styles/main.css` | 全站顏色、字級和首頁樣式。 |
| `src/assets/styles/console.css` | 登入頁和後台樣式。 |
| `src/assets/courseImages.ts` | 課程沒有上傳圖片時，依名稱或風格改用古典、流行、爵士三張預設圖。 |
| `src/assets/images/` | 三張課程預設圖，以及首頁精選老師用的人物圖。 |
| `src/mocks/courses.ts` | 寫死的假課程。只有 `VITE_USE_MOCK_COURSES=true` 時首頁才會用。 |
| `src/mocks/home.ts` | 首頁文案：精選老師、學習流程、常見問題。這些還沒接後端。 |

`src/components/layout/AppHeader.vue`、`src/components/course/CourseCarousel.vue`、`CoursePosterCard.vue`、`CourseImage.vue` 是上一版橫向課程卡，現在沒有頁面引用。目前首頁用的是 `src/components/home/`。

## 假資料和本機資料庫

前端不會直接連 PostgreSQL。

`.env.development` 的 `VITE_USE_MOCK_COURSES=false` 時，首頁呼叫 `GET /api/courses`。這支不用登入，只回資料庫裡狀態是 `published` 的課程，並帶老師姓名。草稿和封存不會出現。課程有上傳圖片就用那張；沒有就用 `src/assets/images/` 的三張預設圖。

改成 `true` 會改看 `src/mocks/courses.ts`，不讀資料庫。

本機若要一次看到很多已發布課程，可在專案根目錄執行 `python scripts/seed_demo_courses.py`。它會建立 30 位老師和 100 堂已發布課程。

## 設計稿

Figma `p6y0aWMsKEwy4ApzcWAuxF`。首頁、登入註冊、老師後台、學生專區、管理員後台已有畫面。搜尋、獨立課程詳情頁，以及 AI 找課推薦尚未完成。
