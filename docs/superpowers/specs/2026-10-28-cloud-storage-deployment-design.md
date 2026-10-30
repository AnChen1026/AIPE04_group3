# 免費共用測試環境與物件儲存設計

日期：2026-10-28。狀態：已依使用者批准完成實作及雲端驗收，詳見 docs/deployment.md。

## 目標與已選方向

使用者選擇 Supabase + Render 免費方案，已建立兩平台帳號，尚無專案或服務。先交付可供全組存取的共用測試環境，匯入既有 426 門虛構課程與 226 位示範老師。這不是正式營運環境；未來正式環境使用獨立資料庫與 bucket，不自動帶入假資料。

方案比較：每位組員本機匯入無法提供即時共享；自管 VPS 需維運與預算；本次採托管 PostgreSQL 與物件儲存，加免費網站服務，減少維運，接受免費額度、休眠及計算資源限制。不承諾免費方案足以提供穩定音訊辨識。

## 系統與環境

- 延續 Vue、FastAPI、SQLAlchemy、Alembic、Session Cookie；不採用 Supabase Auth、不改 JWT。
- 建議單一 Render Docker Web Service，同時供應 Vue 靜態建置與 FastAPI。沿用 `/backend` API／WebSocket 路徑，保留現有 API 的後端路徑。瀏覽器同源，避免兩個網域的第三方 Cookie 問題；現有本機 compose 不受影響。
- Supabase PostgreSQL 為單一課程來源，後端使用 TLS 與適合服務執行環境的連線方式；Alembic 依序升級，不手動改表或另建 AI schema。
- 帳號、訊息、學生資料等應用程式表不經 Supabase 公開 Data API 暴露；僅 FastAPI 伺服器連線。依實際 Supabase 功能關閉／限制 Data API exposed schemas，並驗證匿名 API 無法存取。DB 連線與 Storage 金鑰只保存在後端秘密設定。
- 瀏覽器只取得網站網址；伺服器使用 Secure、HttpOnly、SameSite=Lax Session Cookie。網站使用平台 HTTPS 網域，不需先購買網域。
- 免費方案優先；不建立付費資源、不綁定付款、不升級方案。需要帳號登入、設定新 DB 密碼或 OAuth 新權限時，由使用者完成必要操作。
- 修改範圍含共用 Dockerfile、設定與儲存介面，因使用者已要求部署與檔案儲存整合。本分支不修改與任務無關的功能。

## 儲存模型與權限

物件儲存不是另一套業務資料庫。PostgreSQL 保存檔案 key、檔名、內容類型與既有 metadata；檔案 bytes 放 Storage。

建議第一版所有 bucket 設為 private，依用途區分 `teaching-files`、`profile-images`、`teacher-proofs`。圖片即使對外展示，也由後端現有路由檢查課程／老師狀態後讀取，避免公開 bucket 略過封存與審核權限。學生錄音、作業、MIDI、教材與審核文件不得取得永久公開網址。

新增 storage abstraction，提供寫入、刪除、下載回應、評分所需暫存檔；local adapter 保留開發與測試，Supabase adapter 存取物件儲存。DB 以可辨識的 key 格式區別 local 與 cloud，拒絕越界路徑及任意外部 URL。上傳不使用原檔名作為 key；按類別與使用者 UUID 分層。保持現有擁有者／課程／綁定檢查，再呼叫 Storage。

涵蓋課程參考 MIDI、作業 MIDI／教材、學生錄音、老師照片、課程圖片、老師證明與舊教材路由。學生現有繳交是錄音／音檔；新增「學生 MIDI 繳交」不在此次儲存遷移範圍。

維持現有大小上限與類型規則，補齊轉移造成的回歸測試。私人下載設 no-store；下載回應保留檔名、內容類型與錄音播放所需行為。避免一次把大檔完全載入記憶體，使用串流或受控暫存。評分先下載至每次任務專用暫存目錄，結束時清除。

DB 與 Storage 非同一交易：上傳後 DB 失敗時清理這次新物件；資料庫刪除成功後物件刪除失敗要記錄可重試 key，不回復已完成業務交易，不刪其他人檔案。既有本機檔案如需移轉，先列出引用、複製並驗證雜湊，再更新 key；不直接刪除原始 uploads。

## 假資料匯入

來源是已保存的純假資料快照（原 ai_public_courses / ai_public_teachers，is_demo=true）。不匯出整份本機資料庫，避免帶入真實帳號、密碼、對話、審核文件與金鑰。

沿用先前固定 UUID 命名空間：426 courses，226 users / teacher_profiles / teacher_applications。僅新增缺少資料，不覆寫同 ID 已存在的資料；遇到不相符的 ID／email 衝突則整個交易失敗。示範老師 password_hash=null，不能登入，核准狀態明確為測試用途。每門課保留虛構標示與來源 ID，hybrid 保留文字說明、不假設單一上課方式。

匯入預設 dry-run，指定目標與明確 apply 才寫入；限制共用測試環境，不能在網站啟動時自動 seed。首次寫入前建立可驗證備份；重跑新增應為零。資料快照與匯入工具可放本分支供團隊 review，秘密與完整備份不進 Git。

## 部署、備份與驗收

本機驗證通過後才能部署。Render 使用 production 啟動方式、動態 PORT、健康檢查與非 reload 服務；前端 Node 版本符合 package.json。Secrets 不進建置 context、映像層、Git 或日誌。執行 schema migration 與人工 seed 分開。

資料庫與物件檔案分別備份，建立還原驗證步驟；不將托管 DB 備份誤認為已備份 Storage。容量用量與錯誤日誌納入檢查。

驗收：公開網站 HTTPS、首頁與 426 課程 API、Session 登入／登出與角色權限；老師上傳 MIDI／圖片、學生下載自己教材與上傳音檔、跨帳號拒絕、私人檔案不可匿名下載；重啟服務後檔案仍可讀；seed 重跑無新增；本機 compose 回歸。音訊分析需實測，失敗保持 failed 而非 0 分；無法在免費資源穩定執行時列明限制，不宣稱完整可用。

## 後續擴充

獨立可重試的評分 worker／持久任務佇列、多 instance 聊天 PubSub、檔案掃描與保留期限、自動備份與監控告警，依實際資源與使用量分期導入。此次不新增 Redis、向量資料庫、獨立圖片資料庫或付費計算資源。

## 待取得的外部條件

Supabase 免費 organization／project、建置地區（建議兩平台皆選可用且相近的亞洲地區）、DB 密碼與後端 Storage 連線秘密；Render GitHub repository 授權及部署來源分支。需要使用者持有設定，不能從帳號已建立推定專案已存在。

本文件為實作前設計；使用者確認後再撰寫具體實作計畫並修改程式。Git commit／push／PR 不包含在本次默認授權內。
