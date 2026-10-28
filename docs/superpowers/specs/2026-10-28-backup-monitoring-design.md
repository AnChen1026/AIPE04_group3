# 共用測試站自動備份與監控設計

使用者已批准前一則藍圖並要求開始實作。本輪交付第一、二階段，獨立評分 worker 留到下一階段。不新增付費服務，不更改網站行為或雲端資料表。

## 方案與選擇

使用者採納先做備份再做告警的方向。初期採本機 macOS launchd：沿用現有 Docker PostgreSQL 17 客戶端與私密雲端連線設定，備份放在目前 Supabase 專案之外的本機磁碟。優點是無新增帳號、秘密外送與費用；限制是電腦與 Docker Desktop 必須可用，關機無法執行。GitHub Actions/外部排程需另外將雲端秘密授予其他服務；本輪不採用。未來可將同一套 CLI 移到常駐主機。

## 備份與一致性

每日 Asia/Taipei 09:00，保留最近 7 份成功的受管備份；手動備份與既有檔案不受保留規則影響。不可刪除雲端原始資料或物件。

每份包含 public schema/data custom-format pg_dump、三個 private bucket 原始檔、檔案 SHA-256 manifest、DB row counts、Alembic revision 與 snapshot 中的物件引用。使用 PostgreSQL repeatable-read read-only exported snapshot，pg_dump 與 metadata 讀取共用 snapshot。物件持續使用不可覆寫的 key；複製不到 snapshot 仍引用的檔案、大小或 hash 驗證失敗時整份失敗，不能標示成功。

先寫 private partial 目錄，驗證 dump 可列出、檔案雜湊與引用完整性後原子改名為成功備份。成功後才處理 retention。只清理由工具建立、同來源、且有完成 manifest 的備份，不動未知目錄或手工備份。檔案/目錄權限 0600/0700，內容、秘密、完整備份不進 Git。

還原演練只在獨立的暫時本機 Docker PostgreSQL 17，無外部連接埠，無生產連線／秘密設定；pg_restore public schema/data，對比所有 table row counts、抽查私人檔案與原始 hash，讀取 DB 中的檔案引用核對物件副本。結束移除這次建立的容器。工具不提供將 dump restore 到任意雲端 URL 的選項。

## 監控與告警

每小時讀取整個 DB 大小、所有 Storage bucket 物件大小（避免低估新增 bucket），檢查網站 /health、最近成功備份是否超過 36 小時、清理佇列及超過 15 分鐘的待評分／評分中任務。容量以設定的 DB 500 MB、Storage 1 GB 預算計算，70% warning、85% critical；這些是維運設定，不改網站上傳上限或帳單方案。

任何單一探測失敗仍產生其餘探測結果；失敗不得回填為零用量。不可僅靠 /health 判斷 DB 正常。報告必須包含觀測時間、可用/不可用狀態、容量、備份年齡、告警；不含 DB 密碼、key 或原始 exception 字串。

相同條件的同一嚴重度 24 小時內不重複新增提醒事件；升級嚴重度與恢復立即寫入事件。報告與事件佇列以 private 本機 JSON 保存，搭配 CLI exit status。使用者已選定 Gmail：固定透過 smtp.gmail.com:465、完整 TLS 驗證及獨立應用程式密碼寄送；失敗事件保留待下次重試，可能至少一次送達。

## 排程與操作

兩個 current-user LaunchAgents：每日備份、每小時檢查。plist 只含絕對執行檔、工作目錄與設定檔路徑，不含秘密。安裝/移除及手動執行都有 CLI，安裝檢查系統 timezone 為 Asia/Taipei、Python/Docker 路徑有效。程序鎖避免排程與手動備份重疊；Docker 關閉時寫失敗報告，保留最近成功備份。

本機維運設定與秘密檔分離。使用既有 .env.cloud.json，新的 .env.ops.json 只記目的資料夾、時區、網站 URL、配額及通知偏好。新程式在 feature/backup-monitoring，基於尚未合併的 feature/cloud-storage-deployment。不假定先前對該分支的 commit/push 授權涵蓋本次新分支。

## 驗收

Mock 測試覆蓋 nested/paginated objects、unsafe key、下載/DB failure 不形成成功備份、不觸發 retention、未知資料夾不刪、同來源篩選、hash corruption、告警去重/升級/恢復、獨立 probe failure、秘密不出現在報告或排程。

實際執行一次雲端備份、隔離還原、監控；核對現有共用站 426 published courses 不變；安裝兩個 launchd jobs，print 狀態與人工 kickstart 驗證。記錄首次成功 backup、restore、report 位置與本機依賴限制。

排程使用 ~/Library/Application Support/AIPE04Ops 下的版本化程式與獨立 Python 環境，避免切換 Git 分支移除執行模組；私密設定仍由原工作目錄讀取。檔案欄位契約維護於 scripts/ops/database_refs.py，新增資料庫檔案欄位時須同步更新。
