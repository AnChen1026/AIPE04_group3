# 團隊 Agent 開發規範

| 項目 | 內容 |
| --- | --- |
| 文件版本 | V1.4 |
| 更新日期 | 2026-10-15 |
| 適用對象 | 全組組員，以及 Cursor、Codex、ChatGPT 等 Agent |
| 用途 | 避免跨模組誤改、規格漂移與未驗證的大範圍生成 |

## 1. 必讀順序

開始任何開發任務前依序閱讀：

1. 本文件。
2. `鋼琴教學管理與課程推廣平台_PRD.md`、`SRS功能文件.md`。
3. `SAD系統架構設計.md`。
4. 與本次任務直接相關的 `User_Flow.md`、`資料表設計.md`、`功能製作與分工說明.md`。
5. 實際 Repository 結構與程式碼。

## 2. 最高原則

1. 先理解，再修改。
2. 不直接在 `main` 開發。
3. 不修改其他組員負責的程式。
4. 一次只做當前任務所需的最小修改。
5. 不因更漂亮而重構無關程式。
6. 不把文件中的規劃功能當作已完成。
7. 不確定需求、權限或資料表時先停下詢問。

## 3. V1.4 不可違反的產品規則

- 不串接 LINE。
- 老師與學生以平台帳號登入；一個帳號只有一個固定角色。
- 正式畫面使用 Vue。登入沿用 Session Cookie，不改成 JWT。
- 學生按洽詢建立接洽對話。老師貼綁定碼後，學生才使用該課的教學功能。
- 綁定前後是同一段接洽對話。
- 學生提出約課、請假或調課後，老師同意且時段未被占用前，正式課表不變。
- 每門課一份參考 MIDI。學生以瀏覽器錄音為主，沒有麥克風可上傳音檔。
- 練習回饋與課前摘要分開保存。找課程度不使用練習分數。
- AI 只根據老師提供的出題來源教材產生選擇題與是非題草稿。
- 測驗必須經老師審核後才能發布；作答中不回傳答案，交卷後才批改。
- 完整教材庫與學生教材閱讀不在本輪範圍。

## 4. 目前已知分工與分支

以 2026-10-15 分工、[Issue #24](https://github.com/AnChen1026/AIPE04_group3/issues/24) 與 [Issue #25](https://github.com/AnChen1026/AIPE04_group3/issues/25) 為準。正式畫面使用 Vue，後端使用 FastAPI。登入使用 Session Cookie。Google 登入程式已在，金鑰本輪不要求。

| 負責人 | 負責範圍 | 建議分支 |
| --- | --- | --- |
| 姿彣 | UI/UX | 依該次介面工作指定 |
| Ken | 前端 | 依該次前端工作指定 |
| 禹銨 | 後端與語音 | `feature/login`、`feature/backend`、`feature/ai-practice` |
| 宇鈞 | AI 測驗協作與 Review | 依該次工作指定 |
| 雄 | DevOps | 依該次部署工作指定 |
| Ollie | 資料庫與 AI | `feature/database`、`feature/ai-support` |
| 永富 | AI 測驗流程 | `feature/ai-quiz` |

站內聊天與課前摘要的後端由禹銨整合，畫面由 UI/UX 與前端分工。`feature/messaging` 不再代表站內聊天主責。永富依 [Issue #24](https://github.com/AnChen1026/AIPE04_group3/issues/24) 實作 AI 測驗，宇鈞依 [Issue #25](https://github.com/AnChen1026/AIPE04_group3/issues/25) 協助並 Review。

## 5. 開始前 Context Review

每次任務先執行：

```bash
git branch --show-current
git status
git log --oneline -10
rg --files
```

再確認：

- 使用者是誰，依第 4 節應使用哪個分支。
- 目前實際分支是否正確且不是 `main`。
- 工作區是否有他人未提交變更。
- 任務涉及哪些 Route、Service、Repository、Model、Schema、Frontend 與 Test。
- 是否碰到共用檔案、API Contract、Migration 或跨模組相依。

Agent 修改前先回覆：

```text
Context Review
- 組員／分支：
- 已讀文件：
- 實際相關程式：
- 呼叫流程：
- 文件與實作差異：

Plan
- 最小修改：
- 影響檔案：
- API／Database／Frontend 影響：
- 是否需要跨組協作：
```

## 6. 共用檔案

以下檔案修改前須說明理由與影響：

- `app.py`、正式 FastAPI Entry Point、Router 聚合入口。
- `requirements.txt`、`pyproject.toml`、lock file。
- `package.json` 與 lock file。
- `Dockerfile`、`docker-compose.yml`／`compose.yml`。
- `.gitignore`、`.env.example`、CI／部署設定。
- 共用 Auth、Database Session、錯誤格式與 WebSocket 管理器。
- Alembic Migration 與共用 Model。
- `docs/` 內的 PRD、SRS、SAD、API 與 Data 文件。

## 7. 禁止事項

### 7.1 程式與架構

- 禁止一次生成完整專案並覆蓋現有結構。
- 禁止 Route 直接跨過 Service／Repository 任意存取資料庫。
- 禁止建立第二套重複 Auth、聊天或檔案系統。
- 禁止任意改 API Contract、資料表名稱或 enum。
- 禁止把高風險 AI 功能描述為已驗證完成。

### 7.2 Git

- 禁止在 `main` 直接開發。
- 禁止 `git reset --hard`、force push 與覆蓋他人修改。
- 禁止未經使用者要求就 commit、push、開 PR 或 merge。
- 禁止將 `.env`、金鑰、Token、測試個資或錄音提交。

### 7.3 Database

- 禁止手動修改正式 Schema；使用 Alembic。
- 禁止一次建立所有表而不依功能拆 Migration。
- 禁止 Drop／Rename 既有表而未先確認資料與相依。
- 禁止只依資源 ID 查詢。必須同時限制所屬老師與課程。

### 7.4 AI 與檔案

- 禁止讓 AI 直接決定權限、課表異動或練習分數。
- 禁止讓 AI 自行發布測驗，或在學生交卷前回傳正確答案與解析。
- 禁止使用老師未提供的內容編造測驗題目。
- 禁止將整份不必要個資送進模型。
- 禁止信任副檔名；需驗證 MIME、檔頭、大小與掃描狀態。
- 禁止在低信心鋼琴分析中輸出精密或保證性結論。

## 8. Architecture Consistency

後端延續：

```text
Router / WebSocket Endpoint
    ↓
Service / Business Logic
    ↓
Repository / Data Access
    ↓
SQLAlchemy / PostgreSQL
```

- Request／Response 使用 Pydantic Schema。
- Chat WebSocket 只做即時傳遞；訊息必須由 Service 寫入 Database。
- AI 與音訊分析使用背景任務，不在 HTTP Request 內長時間阻塞。
- 檔案由 storage abstraction 管理，不把大型 binary 存 PostgreSQL。

## 9. Coding Style

- Python 變數與函式：`snake_case`。
- Class：`PascalCase`。
- 常數：`UPPER_SNAKE_CASE`。
- TypeScript 變數與函式：`camelCase`；Component：`PascalCase`。
- 函式以動作命名，例如 `create_course`、`approve_schedule_change`。
- 註解說明商業規則與原因，不逐行翻譯。

重要區塊可使用：

```python
# ======================================================
# 課表異動：老師確認後以交易套用正式課堂
# ======================================================
def approve_schedule_change(...):
    ...
```

## 10. 測試最低要求

依本次變更執行可用項目：

- Syntax／Import／Type check。
- Unit test 與相關 Integration test。
- API 權限與錯誤回應。
- Migration upgrade／downgrade 測試。
- Frontend build 與主要頁面操作。
- WebSocket 斷線重連與越權測試。
- AI Structured Output 驗證與失敗降級。
- 檔案類型、大小、權限與惡意內容測試。

## 11. Commit 規則

- 使用繁體中文，第一句說明實際做了什麼。
- 一個 Commit 盡量只處理一件事。
- 禁止 `update`、`fix`、`完成`、`改一下` 等模糊訊息。

範例：

```text
新增學生調課申請 API，老師確認後才更新課堂
```

Agent 被要求 Commit 時：

1. 先檢查 `git status` 與 `git diff`。
2. 提出中文 Commit 訊息。
3. 等使用者確認後執行。
4. 未經要求不 Push。

## 12. 完成回報

```text
Completed
- 做了什麼。

Changed
- 重要檔案與內容。

Verification
- 執行的測試與結果。

Notes
- 只列 Breaking Change、Migration、環境變數、風險或未完成事項。
```

