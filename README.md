# 鋼琴教學管理與課程推廣平台

AIPE04 Group 3 的專題。老師和學生在同一個網站完成找課、上課與練習；第一版只做鋼琴。

## 目前進度

- 已完成學生／老師註冊、登入、登出、基本資料、角色分流與老師審核（含 Google 登入）。
- 首頁熱門課程與全部課程頁（可篩選、排序）直接讀資料庫裡的已發布課程。
- 已有學生接洽、綁定碼、課表、課務申請及練習錄音的後端 API 與 Vue 畫面。
- 已有老師課程、學生、課表、教材、作業、聊天與測驗等 API 與 Vue 後台。
- 學生送出練習錄音後，後端會在背景用 `backend/audio_scoring` 和該課的參考 MIDI 比對，產生音高、節奏與文字回饋；老師可以在自己的課程看到錄音與回饋。
- 老師可以在每堂課前看課前摘要：整理這位學生從上一堂結束到這一堂開始前，在平台上的練習次數與分數變化。
- 首頁右下角已有可操作的找課助理：最多追問兩題，只從資料庫的已發布鋼琴課程推薦，並可前往既有洽詢流程。
- Vue 正式前端已接上主要找課、登入與課程管理流程；AI 測驗完整流程仍在開發。

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

需要 Docker Desktop。在專案根目錄操作。

### 1. 建立 `.env`

把 `.env.example` 複製成 `.env`。這個檔案不要 commit。

```text
DATABASE_URL=postgresql+psycopg://aipe04:aipe04@localhost:5432/aipe04
TEST_DATABASE_URL=postgresql+psycopg://aipe04:aipe04@localhost:5432/aipe04_test
SESSION_SECRET_KEY=請換成一串自己產生的隨機文字
```

`DATABASE_URL` 維持 `localhost` 即可。用 Docker 啟動時，`docker-compose.yml` 會改連服務名稱 `postgres`。資料庫帳號、密碼、資料庫名稱都是 `aipe04`。

本機要測管理員時，可再加 `ADMIN_EMAIL`、`ADMIN_PASSWORD`。要測 Google 登入時，再加 `GOOGLE_CLIENT_ID`、`GOOGLE_CLIENT_SECRET`、`GOOGLE_REDIRECT_URI`。沒有 Google 金鑰時，網站仍可用 Email 登入。

### 2. 啟動

```powershell
docker compose up --build
```

之後映像沒有改過，只要：

```powershell
docker compose up
```

容器啟動時會自己執行資料庫升級。

- 網頁：http://localhost
- 後端 API 文件：http://localhost:8000/docs

停止：

```powershell
docker compose stop
```

## 測試

PostgreSQL 要先啟動，`.env` 要有 `DATABASE_URL` 與名稱以 `_test` 結尾的 `TEST_DATABASE_URL`。第一次也要先在 `frontend` 執行 `npm install`。在專案根目錄執行：

```bash
python scripts/verify_merge.py
```

驗證程式只允許使用名稱以 `_test` 結尾的獨立測試資料庫，會執行 Migration、後端測試、Model 差異檢查、Vue 程式檢查、型別檢查與正式版建置。目前涵蓋綁定碼、老師與學生的資料隔離、課務申請、公開課程範圍、首頁推薦、課程編輯與參考 MIDI、老師照片與課程圖片、Vue 用的對話與課務 API、練習錄音的評分狀態、課前摘要，以及 Google 驗證導回 Vue。測試不跑真正的音訊辨識，所以跑得很快；真正的音訊辨識用法見 `backend/audio_scoring/README.md`。

## 資料庫開發基準

目前唯一的 Alembic head 是 `011_recommendations`（接在 `010_reference_midis` 之後，`010` 包含參考 MIDI metadata 與既有路徑回填）。Docker 啟動時會自動執行資料庫升級。不要用 `create_all()`、手動建表或修改已共享的 migration。

其他功能新增表時，先同步 main 並執行 `alembic heads`，新 revision 的 `down_revision` 接在當時唯一 head 後面，不要再產生另一條 011。

- 課程共用 `courses`；課前摘要共用 `lesson_preparation_summaries`。
- MIDI 上傳由課程 service 同時更新 `courses.reference_midi_path` 與 `reference_midis`；現有下載與評分仍讀舊欄位。
- `learning_materials` 與 `quizzes` 仍是原型，正式 AI 測驗需另建 migration。
- 資料字典見 [database/data-dictionary](docs/database/data-dictionary.md)，升級、備份及回滾見 [migration runbook](docs/database/migration-runbook.md)。

完整資料庫驗收必須設定 `TEST_DATABASE_URL`，否則 migration 測試會略過。只使用可清除、名稱以 `_test` 結尾的獨立 PostgreSQL；操作步驟見 runbook。GitHub Actions 的 `Database and backend` 工作流程會在 PostgreSQL 16 上執行空庫升級、migration 測試及完整後端測試。

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
| 專案架構、固定開發流程與自行驗證 | `docs/專案架構與開發驗證手冊.md` |
| 專案用語 | `GLOSSARY.md` |
| 老師端後端檔案位置 | `docs/教師端後端模組說明.md` |
| 系統架構 | `docs/SAD系統架構設計.md` |
| 資料表 | `docs/資料表設計.md` |
| 重要決定與原因 | `docs/adr/` |
| 後端檔案分工 | `backend/README.md` |
| 前端頁面與檔案 | `frontend/README.md` |
