# CI 與相依 PR 設計

依使用者同意的順序：補基本 CI、提交功能分支、建立 PR，讓團隊審查後合併。採用既有 GitHub Actions，沿用 PostgreSQL/API 測試，新增前端 lint/type/build、維運 lint/unit tests，以及追蹤檔案防護。替代方案是只開 PR 或立即開 CD；前者缺少自動驗證，後者在分支與 migration 尚未整合前容易部署未驗證版本，因此此輪不採用。

雲端架構先整合目前 origin/main，保留新的音訊行為與 Storage abstraction，以無資料操作的 Alembic merge revision 合併兩條已發布 migration 歷史，不改舊 revision。備份監控再合併雲端分支，以 stacked PR 呈現純維運差異。先合併雲端 PR，再將維運 PR base 改為 main。

CI 僅使用 runner 的暫存 PostgreSQL、模擬 Storage/SMTP，不讀本機秘密、不使用共享庫或寄信。所有 workflow 僅 contents:read。防護檢查拒絕私人 env、備份及金鑰檔，並以 Gitleaks 掃描變更；偵測並非絕對保證，仍須 review。

Render 現在 autoDeployTrigger=off；本輪維持不變。未直接 merge、部署、修改分支保護。團隊需在檢查綠燈後審查合併，再由有管理權的人設定 main 必要檢查及 Render main/checksPass。
