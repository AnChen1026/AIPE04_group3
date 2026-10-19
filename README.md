# 鋼琴教學管理與課程推廣平台

AIPE04 Group 3 的專題。老師和學生在同一個網站完成找課、上課與練習；第一版只做鋼琴。

## 目前進度

- 已完成學生／老師註冊、登入、登出、基本資料、角色分流與老師審核。
- 已有學生接洽、綁定碼、課表、課務申請及練習錄音的後端 API 與 Vue 畫面。
- 已有老師課程、學生、課表、教材、作業、聊天與測驗等 API 與 Vue 後台。
- 學生送出練習錄音後，後端會在背景用 `backend/audio_scoring` 和該課的參考 MIDI 比對，產生音高、節奏與文字回饋；老師可以在自己的課程看到錄音與回饋。
- 老師可以在每堂課前看課前摘要：整理這位學生從上一堂結束到這一堂開始前，在平台上的練習次數與分數變化。
- 首頁推薦的 API 端口已保留在 `/api/recommendations`（格式見 `backend/routers/recommendations.py`），目前回 501，實作由負責首頁推薦的組員完成。
- AI 測驗完整流程仍在開發。

使用者介面都在 `frontend/`（Vue），後端只提供 API。後端使用 FastAPI、SQLAlchemy、Alembic 與 PostgreSQL，登入沿用 Session Cookie，不使用 JWT。

## 分工

| 成員 | 負責 |
| --- | --- |
| 禹銨（組長） | 後端 API、Vue 前端、登入、音訊評分串接與整合 |
| 姿彣 | UI/UX 與畫面流程 |
| 雄 | Docker 與部署 |
| Ollie | 資料表、Migration 與首頁推薦 AI |
| 永富 | AI 測驗出題與批改流程 |
| 宇鈞 | 協助 AI 測驗並 Review 各功能進度 |

## 第一次啟動

需要 Python 3.12 和 Docker。在專案根目錄操作。

### 1. 安裝 Python 套件

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS／Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 啟動 PostgreSQL

```bash
docker compose up -d postgres
```

資料庫帳號、密碼、資料庫名稱都是 `aipe04`，連接埠是 `5432`。

### 3. 建立 `.env`

在專案根目錄新增 `.env`。這個檔案不要 commit。

```text
DATABASE_URL=postgresql+psycopg://aipe04:aipe04@localhost:5432/aipe04
SESSION_SECRET_KEY=請換成一串自己產生的隨機文字
```

本機要測管理員時，可再加 `ADMIN_EMAIL`、`ADMIN_PASSWORD`。要測 Google 登入時，再加 `GOOGLE_CLIENT_ID`、`GOOGLE_CLIENT_SECRET`、`GOOGLE_REDIRECT_URI`（本機設 `http://localhost:3000/backend/auth/google/callback`，驗證完會回到 Vue）。前端和後端不同網址時（例如部署），再加 `FRONTEND_URL`。沒有 Google 金鑰時，網站仍可用 Email 登入。

### 4. 建立資料表並啟動網站

```powershell
alembic upgrade head
python -m backend.main
```

後端在 [http://127.0.0.1:8000](http://127.0.0.1:8000)，只有 API（文件在 `/docs`）。畫面要另外啟動 Vue，見 [frontend/README.md](frontend/README.md)。

## 測試

PostgreSQL 要先啟動，`.env` 要有 `DATABASE_URL`。在專案根目錄執行：

```bash
pytest
```

測試會連到 `.env` 的資料庫，但每個測試結束後整個回滾，不會留下資料。目前涵蓋綁定碼、老師與學生的資料隔離、課務申請、公開課程範圍、課程編輯與參考 MIDI、練習錄音的評分狀態，以及課前摘要。測試會把評分換成假的，所以跑得很快；真正的音訊辨識用法見 `backend/audio_scoring/README.md`。

## 協作

- 不要直接在 `main` 寫功能。
- 在自己的功能分支修改，完成後開 Pull Request。
- `.env`、密碼、API 金鑰、證明文件與錄音不要 push。

## 文件

| 想看什麼 | 檔案 |
| --- | --- |
| 登入註冊現在怎麼跑 | `docs/登入註冊邏輯說明文件.md` |
| FastAPI 怎麼接到 PostgreSQL | `docs/後端串接說明_以登入為例.md` |
| 產品要做哪些功能 | `docs/鋼琴教學管理與課程推廣平台_PRD.md` |
| 功能規格 | `docs/SRS功能文件.md` |
| 使用者怎麼操作 | `docs/User_Flow.md` |
| 分支與 Pull Request | `docs/GitHub團隊協作說明.md` |
| 專案用語 | `GLOSSARY.md` |
| 老師端後端檔案位置 | `docs/教師端後端模組說明.md` |
