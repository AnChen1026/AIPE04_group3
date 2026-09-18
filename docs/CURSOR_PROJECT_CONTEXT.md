# 個人工作室智慧管理平台－Cursor 專案交接文件

| 項目 | 內容 |
| --- | --- |
| 文件版本 | V1.0 |
| 更新日期 | 2026-09-18 |
| 專案階段 | 需求設計完成、開發環境建置中、第一階段功能開始開發 |
| 專案名稱 | 個人工作室智慧管理與課程媒合平台 |
| 主要 TA | 音樂老師、音樂個人工作室 |
| 團隊人數 | 7 人 |
| 本文件用途 | 讓 Cursor 在修改程式前快速理解產品、目前進度、開發範圍與工作規則 |

> 本文件記錄「目前開發狀態與執行原則」，不是用來取代 PRD、SRS、User Flow、Data Schema 或實際程式碼。若文件與程式碼不同，必須先指出差異，不可自行假設哪一方正確。

---

## 1. Cursor 必須先遵守的規則

每次收到開發任務時，依序執行：

1. 先讀本文件、`README`、PRD、SRS、SAD／架構文件，以及與本次任務直接相關的文件。
2. 使用 `rg --files` 或專案目錄檢查實際結構，不可只看單一檔案。
3. 搜尋相關 Route、Service、Repository、Model、Schema、Component、Config 與 Test，理解完整呼叫關係。
4. 先說明最小修改計畫，再開始修改。
5. 延續既有架構、命名、錯誤處理與 API 格式，不因「有更漂亮的寫法」就重構無關程式。
6. 修改後執行相關測試、型別檢查或啟動驗證。
7. 若影響 API、資料庫、環境變數、部署或使用流程，必須同步文件。

不得把本文件列出的「規劃功能」視為「已完成實作」。實際完成度必須由目前 Git 分支、Migration、API、頁面與測試確認。

---

## 2. 專案一句話說明

這是一套以音樂老師與個人工作室為主要對象的課務管理平台，讓老師管理帳號、工作室、課程、學生、課表、堂數與師生訊息；未來再透過單一 LINE 官方帳號與 AI，提供學生綁定、跨工作室查課、請假／調課、人工接管及課程推薦。

---

## 3. 產品要解決的問題

### 3.1 老師端

- 課表、請假、調課、堂數與收款紀錄散落在 LINE、紙本及試算表。
- 老師每天需要重複回答上課時間、剩餘堂數與請假規則。
- 課務異動多靠口頭或訊息確認，缺少可追蹤的同意紀錄。
- 個人老師缺少容易維護的課程曝光與招生工具。

### 3.2 學生端

- 不知道如何描述自己的程度，也難以比較適合的課程。
- 同一位學生可能同時在不同工作室上課，課程資訊分散。
- 請假、調課與聯繫老師缺少統一入口及明確狀態。

---

## 4. 目前最重要的範圍區分

### 4.1 完整 MVP 藍圖

PRD V1.1 與 SRS V1.1 定義的完整 MVP 包含：

1. 公開課程首頁與課程目錄。
2. AI 課程推薦與程度評估。
3. 工作室與課程後台。
4. 學生、課表與規則管理。
5. LINE OA 多工作室綁定與課務查詢。
6. 課程異動與多方同意。
7. AI 客服、人工接管及雙向師生訊息。
8. 堂數與基礎收款紀錄。
9. 課程推廣控制。
10. 平台管理與稽核。

### 4.2 現在正在做的第一階段

目前團隊不是一次完成完整 MVP。第一階段只聚焦於：

| 區域 | 第一階段範圍 | 負責人 |
| --- | --- | --- |
| 平台端 | 登入／註冊 | 永富 |
| 老師端 | 課程管理 | 姿彣 |
| 老師端 | 學生管理 | Ken |
| 老師端 | 訊息接收與處理介面 | Ollie |
| 管理員端 | 平台使用者管理與相關介面 | 宇鈞 |
| 資料庫 | 基礎 Schema 設計與維護 | 禹銨、雄哥 |
| 整合 | 後端框架、資料庫與各模組整合 | 禹銨主導，依團隊協作調整 |

第一階段明確暫不開發：

- 公開首頁課程展示。
- AI 課程推薦。
- 完整 LINE AI 客服與自動課務異動。
- 完整堂數、收款、推廣訂閱及媒合流程。

當本次任務沒有特別指定時，Cursor 應以第一階段為開發邊界，不可自行實作完整 MVP。

---

## 5. 目前進度

### 5.1 已完成或已確認

- 已完成 PRD V1.1、SRS V1.1、User Flow V1.1、資安建議表 V1.1，以及 Data Schema 初步版 V1.1。
- AI 推薦另有流程設計 V0.1，但不是目前第一階段開發項目。
- 已確定後端使用 FastAPI、資料庫使用 PostgreSQL。
- 已確定以 Docker Compose 統一團隊開發環境，不再要求每位成員各自建立 Python venv。
- GitHub 私有 Repository 名稱為 `AIPE04_group3`。
- 已建立或曾建立 `feature/login`、`feature/backend` 等功能分支。
- Windows 成員主要使用 VS Code／Cursor、Docker Desktop；團隊曾討論 WSL2，但實際開發方式應以目前 Repository 的文件與 Compose 設定為準。

### 5.2 尚未能由本交接資料確認

以下項目必須由 Cursor 進入實際 Repository 後檢查，不可直接當成已完成：

- 目前資料夾結構與 Entry Point。
- FastAPI 是否只有測試用 `app.py`，或已拆成正式模組。
- SQLAlchemy Model、Pydantic Schema、Alembic Migration 的完成度。
- 登入／註冊 API 與前端頁面是否已串接。
- PostgreSQL 容器、連線設定與資料表是否已實際建立。
- Next.js 前端是否已初始化，以及各頁面路由的完成度。
- 測試框架、CI、Cloud Run 與 Vercel 設定是否存在。
- LINE Messaging API 與 OpenAI API 是否已建立可執行整合。

### 5.3 Cursor 進入 Repository 後的第一輪檢查

```bash
git status
git branch --show-current
git log --oneline -10
rg --files
docker compose config
docker compose ps
```

接著依實際技術設定檢查：

- Python：`requirements.txt` 或其他 dependency 檔案。
- FastAPI：應用程式 Entry Point、Router 註冊及啟動指令。
- Database：Model、連線設定、Migration 與初始化方式。
- Frontend：`package.json`、Next.js App Router／Pages Router 與 API client。
- Tests：現有測試目錄與執行指令。

若指令與 README 不一致，以現有專案設定為主，並先回報差異。

---

## 6. 目前技術選型

> 下表是團隊已決定或規劃的技術方向；仍須由實際 Repository 驗證是否已落地。

| 層級 | 技術 |
| --- | --- |
| 前端 | Next.js + TypeScript |
| 後端 API | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 |
| Migration | Alembic |
| AI | OpenAI API + Pydantic Structured Output |
| 學生通訊 | LINE Messaging API，單一平台官方帳號 |
| 容器 | Docker + Docker Compose |
| 後端部署 | Google Cloud Run |
| 前端部署 | Vercel |
| 版本控制 | Git + GitHub，功能分支開發後以 PR 合併 |

建議維持的後端依賴方向：

```text
Router / API
    ↓
Service / Business Logic
    ↓
Repository / Data Access
    ↓
SQLAlchemy / PostgreSQL
```

如果現有程式不是這個結構，不可直接大搬家；先說明現況、差異與最小調整方案。

---

## 7. 系統角色

| 角色 | 主要能力 |
| --- | --- |
| 訪客／找課使用者 | 瀏覽、搜尋、AI 諮詢、查看推薦、送出洽詢 |
| 已綁定學生 | 使用 LINE 綁定多個工作室、查課、查堂數、提出異動、聯繫老師 |
| 老師／工作室管理者 | 管理工作室、課程、學生、課表、規則、堂數、訊息與人工案件 |
| 協作老師 | 在被授權的範圍內處理指定課程、學生、異動或訊息 |
| 平台管理員 | 管理平台帳號、內容、異常與稽核，不等同工作室管理員 |

---

## 8. 不可破壞的核心業務規則

即使目前尚未開發到相關功能，資料模型與 API 也不要做出與下列規則衝突的設計：

1. `studio_id` 是主要租戶隔離欄位；後端必須依登入者的工作室成員關係驗證，不能相信前端送來的角色或 `studio_id`。
2. 所有學生共用同一個平台 LINE OA，但以不同 LINE User ID 識別。
3. MVP 中一個 LINE 身份對應一位學生；一位學生可以同時綁定多個工作室。
4. 新增工作室 B 的綁定不可覆蓋工作室 A 的有效綁定。
5. 未指定範圍的「本週課程」查詢，未來要能彙整所有有效綁定工作室並依時間排序。
6. 純查詢可以直接回覆；會修改課堂、老師、出席或堂數的操作必須建立異動申請。
7. 發起送出視為發起人同意；學生與單一老師的異動需要雙方同意，同一工作室跨老師轉課需要三方同意。
8. 異動在全部同意前不可修改正式資料；執行時必須重新驗證版本、權限、時段與堂數，並用單一資料庫交易完成。
9. AI 只負責理解、抽取、追問、摘要與說明，不可直接決定權限、任意查 DB、產生不存在的課程，或跳過同意流程。
10. 老師只能主動聯絡自己工作室內仍有效綁定的學生，送出前須再次確認收件人。
11. 同一 LINE 對話同時只能有一條有效人工路由；結案、切換老師或 24 小時無互動後結束。
12. LINE API 接受訊息只代表平台已送出，不等同學生已送達或已讀。

---

## 9. 初步資料模型

Data Schema V1.1 是討論用初稿，不等同已建立的正式資料庫。主要領域如下：

| 領域 | 初步資料表 |
| --- | --- |
| 帳號與工作室 | `users`、`studios`、`studio_members`、`teacher_profiles` |
| LINE 與學生 | `line_accounts`、`student_profiles`、`studio_student_bindings`、`binding_codes` |
| 課程與時段 | `course_categories`、`courses`、`skill_tags`、`course_skill_requirements`、`course_inquiries`、`teacher_availability_rules`、`availability_exceptions` |
| 課表與規則 | `studio_policies`、`enrollments`、`lesson_sessions`、`session_participants` |
| 異動與同意 | `change_requests`、`change_request_approvals` |
| 堂數與收款 | `lesson_packages`、`lesson_credit_transactions`、`payment_records` |
| 訊息與 AI | `conversations`、`conversation_routes`、`conversation_messages`、`recommendation_sessions`、`recommendation_preferences`、`recommendation_results`、`handoff_tickets` |
| 訂閱與稽核 | `studio_subscriptions`、`outbox_events`、`audit_logs` |

資料庫開發原則：

- 不要一次建立全部資料表；依當前功能需求與 Migration 順序逐步實作。
- UUID 為建議主鍵；主要表建議具有 `created_at`、`updated_at`。
- 時間使用 `timestamptz`，預設顯示時區為 `Asia/Taipei`。
- 金額使用 `numeric(12,2)`，MVP 預設幣別為 TWD。
- Schema 變更必須使用 Alembic Migration，不可手動改正式資料庫結構。
- 關聯、唯一限制、索引、狀態列舉與刪除策略必須先對照 Data Schema 與現有 Migration。
- 若初步 Schema 與目前程式碼不同，先列出差異，不要直接刪表或改欄位。

---

## 10. AI 推薦功能的版本差異

`智慧課程推薦系統流程設計_v0.1.md` 是較早的子系統草案，與目前 PRD／SRS 有以下差異：

| 項目 | 推薦文件 V0.1 | PRD／SRS V1.1 的目前準則 |
| --- | --- | --- |
| 程度名稱 | L1 初學、L2 基礎、L3 中階、L4 進階 | 入門、初階、中階、進階、不確定 |
| 文件描述 | 曾表示尚待決定是否納入 MVP | 完整 MVP 已納入，但第一階段暫不開發 |
| 補問上限 | 程度補問最多 2 題 | 推薦對談最多追問 2 題，實作前需再確認是否包含搜尋條件補問 |

若未來開始實作推薦功能：

- 以 PRD V1.1、SRS V1.1 與最新 API／Schema 文件為優先。
- 不可直接沿用 V0.1 的舊 enum 而不做對照。
- 候選課程必須來自資料庫，流程為「條件篩選 → 規則排序 → 產生說明」。
- 權重、門檻與追問上限應放在後端設定，不寫死在 Prompt。

---

## 11. 資安最低要求

- 密碼只能儲存安全雜湊，不得儲存明碼。
- API Key、Token、Database URL 與 LINE Secret 使用環境變數或 Secret Manager。
- `.env` 不得提交 Git；Log 不得輸出密碼、Token、完整 LINE User ID 或不必要的對話內容。
- 使用 Pydantic 驗證所有 API 輸入；資料庫使用 ORM／參數化查詢。
- 每次工作室資料查詢都要驗證 `studio_id` 與成員關係，避免跨租戶資料外洩。
- LINE Webhook 必須驗證簽章並以事件 ID 去重。
- 綁定碼只保存雜湊，需有期限、次數、撤銷與確認工作室機制。
- 高風險操作、權限變更、課務同意、收款與人工接管需保留稽核紀錄。
- 對外回傳通用錯誤資訊，詳細錯誤只進入受控 Log。

---

## 12. Coding Style 與註解規則

### 12.1 Python 命名

- 變數與函式使用 `snake_case`，例如 `get_user`、`create_course`。
- Class 使用 `PascalCase`，例如 `UserService`、`CourseCreate`。
- 常數使用 `UPPER_SNAKE_CASE`。
- 函式名稱以功能動作命名，避免 `do_something`、`handle_data` 等模糊名稱。

### 12.2 功能區塊註解

重要功能上方可使用團隊約定的區塊標題：

```python
# ======================================================
# 老師 Dashboard：彙總數字與近期清單
# ======================================================
def get_teacher_dashboard(...):
    ...
```

註解應說明「為什麼」與重要商業規則，不要逐行翻譯程式碼。

### 12.3 API 與架構

- 延續既有 Router／Service／Repository 分層；若現有專案尚未分層，先提出最小方案。
- Route 不直接塞入大量商業邏輯或跨多表操作。
- Request／Response 使用明確的 Pydantic Schema。
- 不任意修改既有 API Contract；若需 Breaking Change，先說明影響的前端與其他消費者。
- 錯誤格式、HTTP Status Code、分頁與時間格式應全專案一致。

---

## 13. Git 與團隊開發流程

日常流程：

```bash
git switch main
git pull origin main
git switch feature/<功能名稱>
git merge main

# 開發與測試完成後
git add .
git commit -m "清楚描述本次修改"
git push
```

接著在 GitHub 建立 Pull Request，由負責整合的人檢查後合併到 `main`。

原則：

- 不建議直接在 `main` 開發，即使是組長或主要整合者也一樣。
- Cursor 修改前先確認目前分支與 `git status`。
- 不得覆蓋、刪除或重設其他組員未提交的修改。
- 不執行 `git reset --hard`、強制 Push 或大範圍刪檔，除非使用者明確要求並確認風險。
- 各功能分支合併前先同步 `main`，解決衝突並執行測試。

---

## 14. 開發環境原則

- 團隊以 Docker Compose 統一 Python 與 PostgreSQL 等服務版本。
- 在 Windows PowerShell 直接執行 `python app.py`，使用的是 Windows 本機 Python，不代表已使用容器內套件。
- 若 FastAPI 安裝在容器內，應在容器內執行伺服器，或使用 Compose 的 `command` 自動啟動。
- `docker compose` 指令必須在包含 `docker-compose.yml`／`compose.yml` 的專案目錄執行。
- 修改 dependency 後通常需要重新 Build，不能只 `docker compose start`。

常見流程仍須以 Repository 的 Compose 設定為準：

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f <後端服務名稱>
```

不要假設服務名稱一定是 `python-env`，要先讀 Compose 檔案。

---

## 15. 尚未定案或必須先確認的事項

以下選擇會影響 Schema 或 API，不可由 Cursor 自行決定：

1. 正式專案目錄結構與分層是否已由團隊建立。
2. 第一階段實際要先完成哪些資料表及 Migration 順序。
3. Authentication 採 JWT、Cookie Session 或其他方式，以及 Token 更新／撤銷機制。
4. 工作室成員是否細分到只能管理指定課程或指定學生。
5. 團體課異動是全員同意或一律轉人工。
6. 請假、調課、取消與扣堂規則的正式 JSON Schema。
7. 堂數只允許整數，或允許 0.5 堂。
8. 推薦權重、最低分數及「原工作室有合適課程」的門檻。
9. 對話、課務、收款與稽核資料的正式保留期限。
10. LINE 主動訊息額度、必要通知分類與學生通知偏好。

遇到這些項目時，先搜尋最新文件、Issue、程式碼與 Migration；仍無答案才詢問使用者。

---

## 16. 需求文件優先順序

同一主題有多份文件時，優先順序如下：

1. 使用者本次明確需求與團隊最新會議決議。
2. PRD V1.1：產品目標、範圍、商業規則、驗收條件。
3. SRS V1.1：功能需求與非功能需求。
4. User Flow V1.1：角色操作流程與狀態。
5. Data Schema V1.1：初步資料流與資料表建議；不是正式 Migration。
6. 資安管控建議表 V1.1：最低安全要求。
7. 智慧課程推薦系統流程設計 V0.1：推薦子系統參考，與 V1.1 衝突時不可優先。
8. 現有程式碼與測試：代表目前實作，但若與需求文件衝突必須明確回報。

已知文件問題：

- PRD V1.1 狀態仍是 Draft／待團隊評審。
- SRS 內部分標題與需求文字前有 `x`／`v` 記號，但文件沒有定義其意義，不得把它當成可靠的完成狀態。
- 尚未提供正式 SAD、API Contract、完整 ERD 或 Migration 規格。

---

## 17. 每次任務的建議工作方式

Cursor 收到開發任務後，先用下列格式回應：

```text
Context Review
- 已讀取的相關文件：...
- 實際相關程式：...
- 現有呼叫流程：Frontend → API → Service → Repository → Database
- 文件與實作差異：無／...

Plan
- 修改內容：...
- 影響檔案：...
- API 影響：無／...
- Database 影響：無／需新增 Migration
- Frontend 影響：無／...
- 新增 dependency：無／...
```

完成後使用：

```text
Completed
- 做了什麼。

Changed
- 重要檔案與修改內容。

Verification
- 執行的測試、型別檢查、Build 或啟動結果。

Notes
- 只有 Breaking Change、Migration、環境變數、已知問題或未完成事項才列出。
```

---

## 18. Cursor 第一次加入專案時可直接使用的指令提示

將本文件放在 Repository 根目錄後，可對 Cursor 說：

```text
請先閱讀 CURSOR_PROJECT_CONTEXT.md、README、docs 內的 PRD、SRS、User Flow、Data Schema 與本次任務相關文件，再瀏覽目前專案目錄、Git 分支及程式碼。

先不要修改任何檔案。請先回報：
1. 目前實際架構與 Entry Point。
2. 前端、後端、資料庫、Docker 與測試的完成度。
3. 文件與現有程式碼的差異。
4. 目前最適合優先完成的第一階段任務。
5. 你建議的最小修改計畫。

未經我確認，不要一次實作完整 MVP，也不要做無關重構。
```

---

## 19. 交接給 Cursor 的核心提醒

目前專案是「規格相對完整、程式實作剛起步」的階段。最重要的不是一次寫出所有功能，而是先確認 Repository 現況，讓第一階段的登入、課程管理、學生管理、訊息接收、管理員介面與資料庫基礎能以一致的 API、權限與資料模型順利整合。

請始終遵循：先理解、再修改；優先延續既有設計；只做完成當前任務所需的最小修改。
