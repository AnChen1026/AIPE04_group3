# CI 與 PR 合併流程

每個 PR（包含以功能分支為 base 的相依 PR）與 main push 執行：

| 檢查 | 驗證內容 |
| --- | --- |
| postgres-tests | PostgreSQL 17 空庫 migration、完整 pytest、最後 revision；維運測試存在時也納入 |
| frontend | Node 24、npm ci、lint-check、TypeScript 與 production build |
| source-safety | 拒絕追蹤私人 env／備份／金鑰，Gitleaks 遮蔽掃描本次 commit range |

維運分支另有 `ops-lint`，檢查維運 Python 格式與靜態錯誤。所有工作只授予 contents:read，沒有雲端、Gmail 或 LLM secrets。DB 是 runner 上可丟棄的 PostgreSQL；Storage/SMTP 測試使用 mock。CI 不會備份正式資料、寄信、執行 macOS 排程或部署 Render。

Gitleaks 掃描 PR base 到測試 merge commit 的新增歷史，以及 main push 的 before 到 HEAD；首次 push 無 before 時掃描 HEAD 可達歷史。它不是既有完整歷史稽核，也不能保證識別所有秘密。現有 `frontend/.env.development` 只有公開的 Vite 開關，允許追蹤；私人 `.env.*` 仍應保持 ignored。範本也仍受內容掃描。

## 本次 PR 順序

1. `feature/cloud-storage-deployment` → `main`：私有 Storage、共享測試站、資料匯入與 CI。已整合最新 main 音訊功能，使用 `017_merge_storage_audio` 合併兩個既有 migration head。
2. `feature/backup-monitoring` → `feature/cloud-storage-deployment`：每日備份、隔離還原、Gmail 監控與維運 lint。
3. 第一個 PR 合併後，將第二個 PR 的 base 改為 main。若第一個 PR 使用 squash merge，先以一般 merge 同步 origin/main 並確認 diff 只剩維運變更；不要 force push。
4. 待第二個 PR 的 CI 重新通過，再由團隊審查合併。

未設定自動合併。workflow 本身不等於強制門禁：目前登入者只有 push 權限，無法設定 main 保護。請 repository 管理者在 Rulesets／Branch protection 設定 main 必須經 PR、至少一位 reviewer，並要求上述三項檢查；維運 PR 合併後再加 `ops-lint`。不要在檢查尚未存在的 main 提前要求該檢查。

## CD 後續

`render.yaml` 仍為 `autoDeployTrigger: off`，已開線上測試站仍採人工部署。兩個 PR 合併後，先檢查目標版本、執行備份，再部署與驗收，最後考慮將 Render 連結分支改為 main，Auto-Deploy 改為 After CI Checks Pass（Blueprint 值 `checksPass`）。[Render 文件](https://render.com/docs/deploys#integrating-with-ci) 說明任一 CI 失敗時不自動部署。

本次整合尚未套用到共享庫。升級到合併後程式需執行 Alembic upgrade head，讓現有 `016_storage_cleanup` 取得新的節拍器／對照樂譜欄位。不要只換程式而跳過 migration；不要把新 ORM 連到舊 schema 做正式操作。維運工具的 schema 欄位契約亦須同步。
