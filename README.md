# 鋼琴教學管理與課程推廣平台

AIPE04 Group 3 的專題。老師和學生在同一個網站完成找課、上課與練習；第一版只做鋼琴。

目前 `feature/login` 已可在本機註冊、登入、登出，並分開學生與老師。老師註冊後要等管理員審核。課程、課表、聊天與 AI 功能仍在文件與分工中，還沒全部接上這個網站。

## 分工

以下是 2026-10-05 組長更新的版本。第一版網站使用 Next.js，登入使用 HttpOnly Cookie，並提供 Google 登入。

| 成員 | 負責 |
| --- | --- |
| 禹銨（組長） | 進度、登入系統、AI 音訊辨識、所有後端串接 |
| Ken | 資料庫、確認大家建的表有沒有異常 |
| 雄哥 | Docker、部署、學生端頁面 |
| 姿彣 | 老師端頁面 |
| 宇鈞 | 資安監控、三項 AI 功能的監管顧問 |
| Ollie | 首頁 AI 推薦、首頁客服 |
| 永富 | AI 生成測驗題目 |

正式前端負責人還沒有指定。後端串接先由禹銨負責。站內聊天、課前摘要的主責也還沒有指定。

## 第一次啟動

需要 Python 3.12 和 Docker。在專案根目錄操作。

### 1. 安裝 Python 套件

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

```bash
alembic upgrade head
python3 app.py
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
