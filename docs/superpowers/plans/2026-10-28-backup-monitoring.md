# Backup and Monitoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 可排程、可驗證、失敗不誤報成功的雲端資料備份及維運報告。
**Architecture:** 獨立 Python CLI，從 private JSON 讀取連線。PostgreSQL snapshot＋Storage copy 原子封存，本機 launchd 執行。
**Tech Stack:** Python 3.12 / psycopg / httpx / Docker PostgreSQL 17 / macOS launchd。
**Spec:** docs/superpowers/specs/2026-10-28-backup-monitoring-design.md

## Global Constraints
- 不修改雲端 schema、應用功能或原始檔；不新增付費服務。
- 7 份成功備份；每日台北 09:00；monitor 每小時；70/85% 配額提醒。
- 秘密/備份/報告不進 Git；不對外寄信或發 Webhook，除非使用者選定管道。

## Review Focus
- DB snapshot 引用在複製期間消失：整份失敗，不 prune。
- Windows-style/path traversal/符號連結：不得寫出備份目錄。
- Retention 不刪手工/其他專案/partial backups。
- 服務 probe 失敗不顯示零容量；告警升級與恢復不受 cooldown 阻擋。
- 還原工具無雲端 target、無 host port，只能在自建隔離容器。

### Task 1: Backup engine and isolated restore
**Files:** scripts/ops/{config,storage,postgres,backup,restore}.py, tests/ops/test_backup.py。
**Interfaces:** backup(config)->Path; verify_bundle(path)->dict; restore_check(config,bundle)->dict。
- [x] 建測試：atomic success、失敗保留舊版、hash mismatch、unsafe keys、pagination、retention scope。
- [x] 以 exported snapshot 捕捉 row counts/references 並 pg_dump；Storage streaming 下載，完整驗證後封存。
- [x] 實作 isolated restore，核對 row counts 與檔案引用。
- [x] 執行單元測試與實際 cloud backup/restore。

### Task 2: Reports and alert state
**Files:** scripts/ops/{monitor,cli}.py, tests/ops/test_monitor.py。
**Interfaces:** inspect(config)->dict; update_alerts(report,state,now)->(state,events)。
- [x] 測試 probe failure、容量門檻、過期備份、dedup/escalation/recovery、secret-safe errors。
- [x] 實作 DB/Storage/health probes、報告原子寫入與 exit status；Gmail 加密 SMTP、持久待送佇列與本機報告。
- [x] 真實 readonly monitor，確認不變更共用站資料。

### Task 3: Local schedule and operating guide
**Files:** scripts/ops/schedule.py, docs/operations.md, tests/ops/test_schedule.py。
- [x] 測試 plist 未含秘密、timezone/path guard、作業鎖。
- [x] 安裝 current-user 每日/每小時 LaunchAgents，保存安裝前設定以便回復。
- [x] 手動 kickstart 兩工作，檢查退出碼、成功備份與報告；更新完成紀錄與限制。

## 驗證紀錄
2026-10-28：23 個維運單元測試通過；實際雲端備份及隔離還原核對 28 張表、5 個物件與 5 筆檔案引用。Gmail 測試信經 SMTP 接受，兩個 launchd 工作已安裝並人工觸發驗證。程式碼審查無重大問題。
