# 鋼琴教學管理與課程推廣平台

AIPE04 Group 3 的專題。老師和學生在同一個網站完成找課、上課與練習；第一版只做鋼琴。

## 目前進度

- 已完成學生／老師註冊、登入、登出、基本資料、角色分流與老師審核。
- 已有學生接洽、綁定碼、課表、課務申請及練習錄音的後端流程與 Jinja 測試介面。
- 已有老師課程、學生、課表、教材、作業、聊天與測驗等 API 原型及 Jinja 測試介面。
- `backend/audio_scoring` 可離線分析音高與節奏，但尚未完整接進學生送出錄音的流程。
- 首頁推薦、Vue 正式前端、課前摘要及 AI 測驗完整流程仍在開發。

正式使用者介面規劃使用 Vue；目前 Repository 內的 Jinja 頁面是後端流程測試介面。後端使用 FastAPI、SQLAlchemy、Alembic 與 PostgreSQL，登入沿用 Session Cookie，不使用 JWT。

## 分工

| 成員 | 負責 |
| --- | --- |
| 禹銨（組長） | 後端 API、登入、音訊評分串接與整合 |
| 姿彣 | UI/UX 與畫面流程 |
| Ken | Vue 正式前端 |
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

本機要測管理員時，可再加 `ADMIN_EMAIL`、`ADMIN_PASSWORD`。要測 Google 登入時，再加 `GOOGLE_CLIENT_ID`、`GOOGLE_CLIENT_SECRET`、`GOOGLE_REDIRECT_URI`。沒有 Google 金鑰時，網站仍可用 Email 登入。

### 4. 建立資料表並啟動網站

```powershell
alembic upgrade head
python app.py
```

瀏覽器打開 [http://127.0.0.1:8000](http://127.0.0.1:8000)。

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
