# backend

FastAPI 後端，只提供 API；網站畫面都在 `frontend/`（Vue），不再有 Jinja 模板頁。登入用 Session Cookie，不用 JWT。

## 啟動

入口是 `backend/main.py`。在專案根目錄執行：

```bash
alembic -c backend/alembic.ini upgrade head
python -m backend.main
```

API 在 <http://127.0.0.1:8000>，自動產生的 API 文件在 `/docs`，`/health` 回 `{"status": "ok"}`。資料表一律由 Alembic 建立，網站啟動時不會自動建表。

`.env` 放在專案根目錄：

| 變數 | 用途 |
| --- | --- |
| `DATABASE_URL` | PostgreSQL 連線字串（必填） |
| `SESSION_SECRET_KEY` | 簽署登入 Cookie 的密鑰（必填） |
| `ADMIN_EMAIL`、`ADMIN_PASSWORD` | 有填時，啟動會建立本機管理員帳號 |
| `GOOGLE_CLIENT_ID`、`GOOGLE_CLIENT_SECRET`、`GOOGLE_REDIRECT_URI` | Google 登入。本機 Redirect URI 設 `http://localhost:3000/backend/auth/google/callback`，走 Vue 的 `/backend` 代理 |
| `FRONTEND_URL` | Google 驗證完導回的 Vue 網址。前後端同網址（本機走代理）時不用設 |
| `GEMINI_API_KEY`、`GEMINI_MODEL` | 練習回饋與課前摘要的文字說明。沒填或呼叫失敗時改用規則產生的文字 |

## 分層

一次請求照這個順序走：`routers` 接到網址，`services` 檢查規則，`repositories` 讀寫資料，`models` 對應資料表。

| 位置 | 放什麼 |
| --- | --- |
| `main.py` | 建立 FastAPI、掛 Session 與 CORS、載入所有 router |
| `routers` | 網址與函式的對應。接收 JSON 或 FormData，回傳 JSON |
| `schemas` | 進來和出去的資料格式，例如註冊要有哪些欄位 |
| `services` | 業務規則，例如密碼對不對、綁定碼能不能用、老師能不能核准 |
| `repositories` | 資料庫的查詢與寫入。這裡不判斷業務對錯 |
| `models` | 資料表的形狀。一個 class 對應一張表 |
| `dependencies` | Route 共用的登入、角色與老師身分檢查 |
| `core` | 全站共用設定：讀 `.env`、連線資料庫、密碼雜湊、上傳路徑 |
| `audio_scoring` | 練習錄音評分：錄音和參考 MIDI 比對出音高、節奏分數與文字回饋，見 [audio_scoring/README.md](audio_scoring/README.md) |

新功能在這幾個資料夾各加檔案。不要把 SQL 直接寫在 `routers`。新的 router 記得到 `main.py` 加 `include_router`。

## Router 一覽

| 檔案 | 網址 | 做什麼 |
| --- | --- | --- |
| `auth.py` | `/api/auth/...`、`/auth/google/callback` | 註冊、登入、登出、目前登入者、修改基本資料（老師的姓名會同步到老師個人資料）、修改密碼、Google 登入、Google 老師補送申請、忘記密碼送出申請 |
| `admin.py` | `/api/admin/...` | 審核老師申請、下載證明文件、老師與學生名單、處理忘記密碼申請（重設成臨時密碼） |
| `public_courses.py` | `/api/courses` | 訪客讀已發布課程，不用登入 |
| `images.py` | `/api/images/...` | 已發布課程圖片與已核准老師照片，其他一律 404 |
| `recommendations.py` | `/api/recommendations` | 正式首頁推薦：最多追問兩題，只回傳已發布課程 |
| `student.py` | `/api/student/...` | 學生：接洽對話、綁定碼、課表、課務申請、練習錄音與回饋 |
| `chat_ws.py` | `/ws/conversations/{id}`（WebSocket） | 接洽對話即時訊息。先寫資料庫，再推給在線的人 |
| `teacher_profile.py` | `/teacher/me`、`/teacher/profile`、`/teacher/photo` | 老師個人資料與照片 |
| `teacher_courses.py` | `/courses/...`、`/teacher/courses` | 老師的課程：新增、修改、封存、課程圖片、參考 MIDI |
| `teacher_students.py` | `/teacher/students`、`/teacher/courses/{id}/students/{id}/unbind` | 已綁定的學生、解除綁定 |
| `teacher_chat.py` | `/teacher/conversations/...` | 老師的接洽對話：列表、讀寫訊息、發綁定碼 |
| `teacher_inquiries.py` | `/teacher/inquiries` | 洽詢中的學生 |
| `teacher_lessons.py` | `/teacher/lessons`、`/teacher/change-requests` | 課表、課務申請同意或拒絕、課前摘要 |
| `teacher_practice.py` | `/teacher/courses/{id}/recordings`、`/teacher/recordings/{id}/audio` | 老師看自己課程的練習錄音與回饋 |
| `teacher_materials.py`、`teacher_quizzes.py` | `/teacher/materials`、`/teacher/quizzes` | 教材與測驗（AI 測驗由負責的組員開發） |
| `health.py` | `/health` | 確認服務有在跑 |

老師端資料同步集中在 `services/teacher_sync.py`，檔案上傳路徑集中在 `core/uploads.py`。學生送出錄音後，`services/practice.py` 會在背景呼叫 `audio_scoring/scorer.py` 評分；分析失敗記成失敗，不記 0 分。

## 測試

測試在根目錄 `tests/`，連 `.env` 的資料庫，每個測試都包在交易裡，結束後回滾，不留資料。

```bash
uv run --with pytest --with httpx python -m pytest tests -q
```
