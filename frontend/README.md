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

打開 <http://localhost:3000>。要讀登入狀態時，另外在根目錄啟動後端（`python app.py`，port 8000）。開發伺服器會把 `/api` 轉給後端，Session Cookie 才會一起帶過去。

## 指令

| 指令 | 用途 |
| --- | --- |
| `npm run dev` | 開發伺服器 |
| `npm run build` | 型別檢查並打包到 `dist/` |
| `npm run lint` | oxlint 與 ESLint |

## 檔案說明

`node_modules/`、`dist/` 是工具產生的，下面不列。

| 檔案 | 做什麼 |
| --- | --- |
| `index.html` | 網站進入點。瀏覽器先打開這個檔，再載入 Vue。 |
| `package.json` | 專案用到的套件，以及 `npm run` 的指令。 |
| `package-lock.json` | 鎖定套件版本，讓每台電腦裝到同一版。要留著。 |
| `vite.config.ts` | 開發伺服器設定。`/api` 會轉到本機後端 `http://127.0.0.1:8000`。 |
| `tsconfig.json` | TypeScript 總設定，再交給下面兩個檔。 |
| `tsconfig.app.json` | 檢查 `src/` 裡的 Vue 與 TypeScript。 |
| `tsconfig.node.json` | 檢查 `vite.config.ts` 這種給 Node 跑的設定檔。 |
| `env.d.ts` | 告訴 TypeScript：`.vue` 檔和 `VITE_` 環境變數是合法的。 |
| `.env.development` | 只有開發時生效。現在用它決定首頁要不要顯示假課程。 |
| `eslint.config.ts` | ESLint 的程式風格規則。 |
| `.oxlintrc.json` | oxlint 的檢查規則。`npm run lint` 會先跑它。 |
| `.editorconfig` | 存檔時用 2 個空白縮排、檔尾換行。 |
| `.gitattributes` | 讓 Git 把文字檔的換行統一成 LF。 |
| `.gitignore` | 不要上傳的檔，例如 `node_modules/`、`dist/`。 |
| `public/favicon.ico` | 瀏覽器分頁上的小圖示。 |
| `src/main.ts` | 啟動 Vue，接上路由和 Pinia。 |
| `src/App.vue` | 全站外框：頁首、目前頁面、右下角 AI 按鈕。 |
| `src/router/index.ts` | 網址對應哪個頁面。除了首頁，其他先去「開發中」。 |
| `src/views/HomeView.vue` | 首頁。依風格分成橫向課程列。 |
| `src/views/ComingSoonView.vue` | 還沒做的頁面共用這一頁。 |
| `src/components/layout/AppHeader.vue` | 頁首：站名、搜尋、登入。 |
| `src/components/course/CourseCarousel.vue` | 一列課程，左右箭頭可切換下一排。 |
| `src/components/course/CoursePosterCard.vue` | 單張課程卡。滑鼠移上去顯示完整資訊和「與老師聯繫」。 |
| `src/components/course/CourseImage.vue` | 卡片圖片。沒有圖時顯示鋼琴鍵盤佔位圖。 |
| `src/components/common/AiAssistButton.vue` | 右下角「AI協助」。視窗還是提示文字，尚未推薦課程。 |
| `src/api/http.ts` | 所有後端請求的共同寫法，會帶登入 Cookie。 |
| `src/api/courses.ts` | 取得課程。開發時可改走假資料。 |
| `src/api/auth.ts` | 問後端「現在是誰登入」和登出。 |
| `src/stores/auth.ts` | 把目前登入者記在前端。 |
| `src/types/course.ts` | 課程資料的欄位形狀。 |
| `src/types/user.ts` | 登入者的欄位形狀。 |
| `src/mocks/courses.ts` | 10 筆寫死的假課程，只給排版用。 |
| `src/assets/styles/main.css` | 全站顏色、字級和共用樣式。 |
| `src/assets/courseImages.ts` | 依課程名稱或風格挑選素材圖。 |
| `src/assets/images/` | 古典、流行、爵士三張課程圖。 |

## 假資料和本機資料庫

前端不會直接連 PostgreSQL。首頁要看到課程，必須請後端 API 查資料庫。

`.env.development` 的 `VITE_USE_MOCK_COURSES=false` 時，首頁呼叫 `GET /api/courses`。這支不用登入，只回資料庫裡狀態是 `published` 的課程，並帶老師姓名。草稿和封存不會出現。圖片用 `src/assets/images/` 的三張素材，依名稱或風格對應。

改成 `true` 會改看 `src/mocks/courses.ts` 的 10 筆假課程，不讀資料庫。

## 設計稿

Figma `p6y0aWMsKEwy4ApzcWAuxF` 的 Page 2。目前完成「首頁」，其他頁面先導到開發中頁面。
