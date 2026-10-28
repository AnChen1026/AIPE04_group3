# 團隊共用測試環境

本分支目標是 Supabase PostgreSQL + private Storage + Render Free。設定檔存在不代表已上線；實際專案、網址與驗收結果另記於文末。帳號、服務由團隊持有。

## 團隊日常流程

一般驗收只開共用網站，各自以學生／老師帳號登入。開發者使用自己的 Docker PostgreSQL、local storage 與假資料，不把破壞性測試指向共享庫。Git 分支不隔離 DB。只有維運人員管理 DB migrations、秘密設定與備份；Supabase 後台以個別邀請管理，不共享個人 GitHub 帳號。

正式營運另建環境；本環境只能放虛構課程與測試資料。免費服務有休眠、配額與資源限制，不承諾營運 SLA 或音訊辨識可穩定執行。

## 資源與存取

- Supabase 專案：建議 `aipe04-group3-staging`，Free，亞太地區。
- 建專案時關閉 **Enable Data API**。FastAPI 使用 SQLAlchemy 連線；瀏覽器不可直接使用 DB 或 Storage 伺服器金鑰。
- Storage 建立 `teaching-files`、`profile-images`、`teacher-proofs`，全部 **private**；不加匿名讀寫 policy。後端以 server secret 經 Storage API 存取；圖片也經既有狀態與權限路由提供。
- 檔案 key：`storage://bucket/category/user-or-resource-id/random-name.ext`，DB 僅存位置。參考 MIDI 2 MB、圖片 5 MB、錄音 20 MB、作業教材單檔 30 MB、證明文件 5 MB。舊教材入口單檔也限制 30 MB。
- 現有功能是老師上傳參考 MIDI，學生交錄音／音檔；此次不新增學生 MIDI 繳交功能。
- 匿名使用 Supabase REST endpoint 不應讀到應用程式 tables；私有 bucket 的 public URL 不得下載物件。這兩項必須在實際專案驗證。

## 部署

1. 本分支修改審查與驗證後，由有 repo 權限者 commit/push；本專案規範要求使用者明確授權 Git 發布。
2. 在 Supabase Connect 取得 Session pooler（5432）連線資料，適合 IPv4 部署；密碼需 URL encode。使用 `postgresql+psycopg`、TLS `sslmode=verify-full`。下載專案 DB CA 憑證，設定 `SUPABASE_DB_CA_CERT` PEM 內容，連線字串加 `sslrootcert=/tmp/supabase-ca.crt`。不關閉憑證驗證。
3. Render Blueprint 使用 `render.yaml`，免費 web service、Singapore、Dockerfile `deploy/Dockerfile`、build context repository root。指定本分支或已審查的合併版本；不使用目前還沒有部署程式的 main。
4. Render Environment 填 `.env.cloud.example` 所列設定，另填 `SUPABASE_DB_CA_CERT`。`SUPABASE_SECRET_KEY` 只用於後端，可用 Supabase server secret 或 legacy service_role JWT。不要使用 publishable/anon key，也不把任何 server secret 放在 `VITE_` 變數。
5. 設定獨立管理員 email 與強隨機密碼；不沿用範例 admin 密碼。啟動只跑 migration，不自動匯入假資料。
6. Docker 執行非 root，使用 Uvicorn 正式入口與動態 PORT。單一免費 instance 啟動時先 migrate；將來多 replica 必須改為單獨 release migration，聊天也需要 PubSub。
7. 同源網站根路徑供應 Vue，`/backend` 轉給 API/WebSocket，`/health` 健康檢查。Google OAuth 若啟用，更新 Google 允許 callback 與 `GOOGLE_REDIRECT_URI=https://SITE/backend/auth/google/callback`。

免費 web service 沒有可靠持久磁碟：只允許評分／下載使用暫存；原始檔一律 Storage。音訊相依套件較重，須實際測量 RAM／評分；未通過時應保留失敗狀態與限制說明，不宣稱已完整支援。

## 假資料匯入

使用 `scripts/data/aicourse-demo.json`，來源為純虛構 AICourseFinder 快照（208 teacher profiles、426 courses，18 位課程老師補建後共 226 位）。不搬本機使用者、對話、密碼、向量或整份 DB。

本機維運可將雲端環境變數存為 `.env.cloud.json`（已被 Git 忽略，限制檔案權限），JSON key 使用 `.env.cloud.example` 的名稱；CA 憑證以 JSON 字串保存換行。不要直接覆寫本機 `.env`。

```bash
python -m scripts.cloud_command --config .env.cloud.json validate
python -m scripts.cloud_command --config .env.cloud.json migrate
python -m scripts.cloud_command --config .env.cloud.json seed
python -m scripts.cloud_command --config .env.cloud.json seed --apply --confirm-database postgres
```

維運工具以結構化 JSON 載入，不透過 shell 展開秘密。`validate` 只驗證設定，仍需實際測試 DB 與 Storage 連線。

先以目標連線環境執行 migration 與 custom-format pg_dump 備份，確認備份可列出且可在隔離庫還原。不要把密碼放進 CLI 參數或 shell history；以私有環境檔／PGSERVICE／PGPASSFILE 配置 PostgreSQL 工具。

```bash
python -m scripts.import_demo_data
# 核對目標與試跑新增數量，首次預期 users/profiles/applications 各 226、courses 426
python -m scripts.import_demo_data --apply --confirm-database postgres
python -m scripts.import_demo_data
# 第二次預期所有新增數皆 0
```

APP_ENV 僅允許 local/staging。固定 UUID，只新增，不覆寫既有課程或帳號；碰撞整批 rollback。示範老師不可登入，保留虛構標示。先前已匯入本機的資料應回報零新增。

## 舊檔案搬移與刪除重試

若來源 `uploads/` 已有真實檔案，不可直接把本機 DB dump restore 到雲端就算完成。先列出所有引用（含 reference_midis.storage_key、錄音歷史參考 MIDI、proof 省略 uploads/ 的舊格式），比對存在性；用 `scripts.migrate_uploads` dry-run，再 apply。搬移期間暫停來源引用資料的寫入。工具按來源相對路徑雜湊＋內容雜湊命名，複製到 Storage 並讀回核對 SHA-256，單一 DB transaction 更新引用，不刪原始檔。失敗時 DB rollback；已成功複製但尚未被引用的物件可重跑重用，需在維運紀錄追蹤。

DB commit 失敗會清理新物件。刪除失敗寫進 `storage_cleanup_jobs`，維運執行：

```bash
python -m scripts.retry_storage_cleanup
```

每次最多 100 筆，成功移除 job，失敗累計 attempts。不提供公開 HTTP 清理入口。

## 備份、還原與驗收

DB 備份不包含 Storage bytes。DB 使用 pg_dump custom format；Storage 另以具唯讀權限的工具備份三個 bucket 到受控位置，保留 key 與 SHA-256 manifest。至少在重大資料變更前備份；演示週每日備份，容量與保留天數由維運依額度管理。不得將私有檔案或完整備份提交 Git。

還原演練：在隔離 DB restore，再還原物件至隔離 bucket／專案，核對引用、雜湊、課程數與角色權限，最後測試私人下載。不能僅以 pg_dump 命令成功宣稱可恢復。

驗收項目：HTTPS 網址、Secure Cookie、426 公開課程、登入登出、師生權限、匿名 Data API 拒絕、私有物件匿名拒絕、MIDI/圖片/教材/錄音上傳下載、Range 播放、越權拒絕、重啟後仍可讀、seed 重跑零新增。真實音訊評分與雲端服務必須另記實測結果。

## 目前外部狀態

- 2026-10-28：已建立 Free organization `AIPE04 Group 3` 與專案 `aipe04-group3-staging`（`eemekhsexmntnkxvunph`，Tokyo）。使用者已親自完成 DB 密碼設定。
- 已完成雲端 Alembic 升級至 `016_storage_cleanup`，匯入 426 門課程與 226 位示範老師；重跑新增皆為 0。
- 已建立三個 private bucket，實測匿名下載拒絕；Data API 控制台為關閉，REST 無法查詢資料。
- 共用網站：https://aipe04-group3-staging.onrender.com ，課程頁 `/courses`，API 文件 `/backend/docs`。
- Render 免費服務：`srv-dbgov2nf3r2c73aacvdg`；Blueprint：`exs-dbgorcon74is73d20pgg`。程式執行版本 `6900101`，後續純文件 commit 不影響執行程式。
- Supabase 控制台的 main / Production 是平台內建資料庫分支標籤；本專案 APP_ENV 仍為 staging，未建立正式營運環境。
- 功能分支已經使用者授權 commit/push；尚未合併 main，也未建立 PR。Render Auto Deploy 為關閉，後續程式更新須選 Manual Deploy → Deploy latest commit。

## 網站管理與測試帳號

管理員是使用者指定的個人 email，網站登入帳密另存本機 `.env.cloud.admin.json`（與 Supabase DB 密碼不同）。只有維運人員使用管理員；組員可以在共用網站各自註冊，老師由管理員核准。

另外建立 1 位測試老師、2 位測試學生，帳密存 `.env.cloud.test-accounts.json`；驗收課程已封存，不影響公開 426 門課。原 226 位示範老師仍無登入密碼。這些私密檔案與 `.env.cloud.json`、`.env.cloud.password`、`.env.cloud.server-key` 全部被 Git 忽略且檔案權限為 0600。不要把完整雲端連線設定分享給一般測試者。

## 雲端驗收紀錄（2026-10-28）

- HTTPS 首頁、HEAD、課程頁、健康檢查、426 公開課程通過。
- 管理員與測試師生登入／登出、Secure + HttpOnly Session Cookie 通過。
- 實際圖片、課程 MIDI、作業 MIDI／PDF 教材、學生錄音上傳與下載通過；草稿與封存圖片、未綁定與其他學生越權讀取均拒絕。
- 學生錄音 byte Range 206、對應老師回放通過；1 秒合成音檔的背景評分 completed。這不是長錄音或多人並行壓力測試，不承諾免費服務可承擔正式用量。
- Render 於 14:11（Asia/Taipei）手動重啟，事件顯示 Service restarted；重啟後首頁、課程、私人錄音與作業 MIDI 仍可讀取。
- 雲端 `public` schema/data 備份在隔離 PostgreSQL 還原成功，426 已發布課程及錄音可查。三個 bucket 另備份 5 個物件，共 45,091 bytes，逐一核對 SHA-256。備份位於被 Git 忽略的 `db-backups/`。
- 2026-10-28 已於維運者 Mac 安裝每日備份、每小時監控及 Gmail 告警；執行方式與本機可用性限制見 [維運手冊](operations.md)。


## 本機驗證紀錄（2026-10-28）

119 項後端測試通過（含獨立 PostgreSQL 的 migration 升降版、Storage mock 與跨帳號拒絕）；Alembic check 無差異；前端 lint-check、型別與正式 build 通過；完整雲端映像 build 成功。以該映像在 512 MiB 容器啟動，Vue SPA、API、426 課程匯入及重跑零新增驗證通過，閒置記憶體約 76 MiB。此段是本機驗證；實際雲端驗收另見上節，未測音訊評分峰值。
