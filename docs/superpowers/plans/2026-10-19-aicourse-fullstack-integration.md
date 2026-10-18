# AICourse Full Stack Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將對話式鋼琴找課整合至正式 FastAPI、PostgreSQL 與 Vue，完成可合併的端到端功能。

**Architecture:** 使用正式 `courses` 作為唯一課程來源，Alembic 011 保存匿名推薦對談及帶外鍵的推薦結果。後端以明確文字規則抽取條件並產生可追溯理由；Vue 既有 AI 面板負責對談與洽詢導流。

**Tech Stack:** FastAPI、SQLAlchemy 2、Alembic、PostgreSQL、Pydantic、Vue 3、TypeScript、Vite

**Spec:** `docs/superpowers/specs/2026-10-19-aicourse-fullstack-integration-design.md`

## Global Constraints

- 只處理鋼琴，且只回傳正式資料庫的已發布課程。
- 整次推薦最多追問兩題；訪客沒說的條件維持未知。
- 練習分數不得改變找課程度或推薦結果。
- 沿用 Session Cookie，不建立第二套登入。
- Alembic 新版必須接在 `010_reference_midis` 之後。

## Review Focus

- 訪客指定條件但課程欄位為空時，該課程不得被當作符合。
- 草稿及封存課程永遠不得出現在推薦結果。
- 猜測、問句與否定內容不得被誤存成已確認條件。
- 第二次追問後必須結束追問，即使仍有未知條件。
- 猜測 session UUID 或換瀏覽器不得讀取別人的對談。

---

### Task 1: 推薦資料表與 Migration 011

**Files:**
- Modify: `backend/models/student.py`
- Modify: `alembic/env.py`
- Create: `alembic/versions/011_recommendation_sessions.py`
- Test: `tests/database/test_recommendation_migration.py`

**Interfaces:**
- Produces: `RecommendationSession`、`RecommendationItem` ORM models。

- [x] 先寫 010→011 Migration 測試，驗證表、限制、外鍵與降級。
- [x] 執行測試並確認尚未有 011 時失敗。
- [x] 建立 ORM 與 Migration；`question_count` 限制為 0 到 2，推薦項目外鍵指向正式課程。
- [x] 執行 Migration 測試並確認通過。
- [x] 納入本階段整合提交。

### Task 2: 對談理解與推薦服務

**Files:**
- Create: `backend/services/recommendation.py`
- Test: `tests/test_recommendations.py`

**Interfaces:**
- Produces: `start_recommendation(db, owner_key, message)`、`answer_recommendation(...)`、`read_recommendation(...)`。

- [x] 寫失敗測試：已發布限制、最多兩問、未知條件、空欄位不符合、非鋼琴、瀏覽器隔離。
- [x] 實作明確條件抽取、追問狀態及最多三門課程的穩定排序。
- [x] 保存訊息、條件及帶課程外鍵的結果；重新計算時替換舊結果。
- [x] 執行服務與完整後端測試。
- [x] 納入本階段整合提交。

### Task 3: 正式 Recommendation API

**Files:**
- Modify: `backend/routers/recommendations.py`
- Modify: `app.py`
- Test: `tests/test_recommendations.py`

**Interfaces:**
- Consumes: Task 2 服務。
- Produces: 既定三個 `/api/recommendations` JSON 端口。

- [x] 寫 API 失敗測試，涵蓋建立、回答、讀取、驗證錯誤與他人 session。
- [x] 以既有簽章 Session Cookie 建立瀏覽器擁有者並呼叫服務。
- [x] 移除 501 stub，保留現有回傳欄位並加入前端需要的描述與圖片欄位。
- [x] 執行 API 與完整後端測試。
- [x] 納入本階段整合提交。

### Task 4: Vue AI 找課面板

**Files:**
- Create: `frontend/src/api/recommendations.ts`
- Create: `frontend/src/types/recommendation.ts`
- Modify: `frontend/src/components/common/AiAssistButton.vue`

**Interfaces:**
- Consumes: Task 3 Recommendation API。
- Produces: 首頁可操作的對談、條件、推薦卡與洽詢導流。

- [x] 建立 TypeScript API 型別及三個端口呼叫。
- [x] 將既有提示面板改成可送出訊息、顯示追問與推薦結果的對談面板。
- [x] 加入載入、錯誤、空結果及重新開始狀態，推薦 CTA 使用 `/courses/:id/contact`。
- [x] 執行 `npm run type-check`、`npm run build-only` 與本次檔案 lint。
- [x] 納入本階段整合提交。

### Task 5: 合併驗證與交接

**Files:**
- Modify: `README.md`
- Modify: `docs/database/data-dictionary.md`

**Interfaces:**
- Produces: 可審查 PR 與操作說明。

- [x] 從空白 PostgreSQL 升級 001→011，執行 `alembic heads` 與 `alembic check`。
- [x] 執行所有後端測試與 Vue build/type-check、本次檔案 lint。
- [x] 更新資料字典、啟動方式與無模型金鑰時的行為。
- [ ] 檢查 diff、提交、推送並建立以 `feature/frontend` 為目標且標明依賴 PR #29 的 PR。
