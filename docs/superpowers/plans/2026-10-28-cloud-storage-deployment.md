# Cloud Storage Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立免費共享測試網站、私有檔案儲存與可重做假資料匯入。
**Architecture:** 單一 Render Docker service 提供 Vue SPA 與 FastAPI，同源 /backend proxy prefix。Supabase 提供 PostgreSQL 及私有 buckets；本機繼續 local storage。
**Tech Stack:** Vue / Node 24, Python 3.12 / FastAPI / SQLAlchemy / Alembic, Supabase Storage REST, httpx。
**Spec:** docs/superpowers/specs/2026-10-28-cloud-storage-deployment-design.md

## Global Constraints

- 保留 Session Cookie 與既有 Route/Service 權限；不可自動 seed 或覆寫已存在資料。
- 不 commit/push/PR；不付費。使用者已要求直接執行，本 session 自行依序實作驗證。
- 雲端金鑰只進伺服器秘密設定，Data API 不暴露應用程式 tables。
- 本機 compose 可持續使用；既有 uploads 不刪除。

## Review Focus

- path traversal / SSRF：storage key 只接受允許 bucket 與正常相對 key。
- DB commit 失敗：新物件清理；cleanup 失敗保存於 DB retry queue。
- 私人下載與 Range：檢查擁有者後交由 FileResponse，暫存結束清理。
- seed collision：修改既有 UUID/email 時失敗，整批 rollback；重跑不覆寫。
- 雲端重啟：不依賴 uploads 或本機 retry log，測試 remote readback。

### Task 1: 統一儲存與整合
**Files:** backend/core/storage.py, backend/core/uploads.py; backend/services/{course,student,assignment,images,teacher,practice}.py; backend/routers/{student,teacher_courses,teacher_practice,assignments,images,admin,teacher_materials}.py; tests/test_storage.py; backend/models/storage_cleanup.py; backend/alembic/versions/016_storage_cleanup.py。
**Interfaces:** save_file(path: Path, content: bytes, content_type=None)->str; delete_file(value: str)->None; file_response(value: str, **kwargs)->Response; local_file(value: str)->ContextManager[Path]; cleanup_files(values: list[str])->None。
- [x] 新增測試並執行 red：local/remote 寫讀刪、path traversal、404/timeout、temporary cleanup、Range、API 越權。
- [x] 實作 local + Supabase REST adapter，限制 bucket/key、下載到 tempfile、private cache header、受控 exception。
- [x] 替換所有上傳、下載、評分與刪除呼叫，DB 失敗清新物件，雲端 cleanup queue 持久化與 retry CLI。
- [x] 執行新測試與既有檔案／作業／權限測試。

### Task 2: 可重做資料匯入
**Files:** scripts/import_demo_data.py, scripts/data/aicourse-demo.json, tests/test_demo_import.py。
**Interfaces:** import_demo(db: Session, source: dict)->dict；CLI dry-run default，--apply --confirm-database NAME，APP_ENV=staging/local。
- [x] 測試 426/226、第二次零新增、碰撞整批 rollback、原有資料保持、production 拒絕。
- [x] 從純假資料快照轉製，固定既有 UUID 與保留測試標示，新增無登入密碼 users。
- [x] 隔離 test DB 試跑，不對目前網站資料做破壞性測試。

### Task 3: 部署入口與操作手冊
**Files:** deploy/Dockerfile, deploy/start.sh, backend/cloud_app.py, render.yaml, .dockerignore, .env.cloud.example, docs/deployment.md, tests/test_cloud_app.py。
**Interfaces:** backend.cloud_app:app 支援 /backend 與 WebSocket 同源路徑，/health 公開，SPA fallback 不吃 API。
- [x] 測試 API prefix、SPA traversal、Secure Cookie 與未知 API 404。
- [x] Node 24 前端 build、非 reload Uvicorn、PORT、HTTPS Cookie、TLS DB；建置不含 env/uploads/backups。
- [x] 部署免費 Supabase/Render；使用者交接 DB 密碼、GitHub 授權，需 push 時另行要求既定 Git 授權。
- [x] DB backup/restore、private bucket、Data API 限制、seed dry-run/apply、重啟持久性驗收。未取得外部條件不得宣稱上線。

實際完成與限制見 docs/deployment.md。使用者已授權 commit/push 此功能分支；未合併 main。
