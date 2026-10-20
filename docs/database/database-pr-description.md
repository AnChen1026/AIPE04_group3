目前 main 僅有 Alembic 009，參考 MIDI 缺少獨立 metadata。本變更新增 010，回填既有 MIDI 路徑，並讓上傳同一交易同步保存課程路徑、原始檔名、SHA-256 與大小；既有下載及評分沿用舊欄位。

已整合 main `2fa1a28` 並解決資料表文件衝突。修正 migration 降版測試污染後續 API 測試，以及 metadata 查詢失敗遺留新檔案的問題。補上 PostgreSQL CI、資料字典及新功能接續 migration 的交接規則。

驗證：Python 3.12／隔離 PostgreSQL 16 完整後端 **58 passed，0 skipped**；空庫升級、009→010 回填、010→009→010、唯一 head、雙寫及查詢／提交失敗保留原檔皆通過。`git diff --check` 與 main 合併模擬通過。遠端 CI 尚待執行。

合併範圍僅到 `010_reference_midis`，不含另一分支的首頁推薦 011。部署先備份並執行 `alembic upgrade head`，依 runbook 檢查回填；MIDI 檔案仍存於主機，物件儲存與正式環境備份治理不在本次範圍。
