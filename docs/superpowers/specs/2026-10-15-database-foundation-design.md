# Issue #18 資料庫基礎設計

## 目的

本階段補齊 Issue #18 尚缺的參考 MIDI 與課前摘要資料結構，並建立可重複驗證的 Alembic Migration 流程。這是後續統一老師端課程資料與整合 `feature/AICourseFinder` 的基礎。

## 已確認範圍

- 採保守整合。
- 接在 `origin/feature/backend` 的 `006_message_client_id` 之後新增 `007_database_foundation`，不修改既有 `001` 至 `006`。
- 新增一對一的 `reference_midis`，一門課最多一份參考 MIDI。
- 新增 `lesson_summaries`，一堂即將上課的正式課堂最多一份課前摘要。
- Migration 會把既有 `courses.reference_midi_path` 搬入 `reference_midis`。
- Service 在過渡期同時寫入舊欄位與新表，讓現有學生及老師測試頁繼續運作。
- 本工作不額外刪除老師端舊表，並保留 `Base.metadata.create_all()`。上游 `005_unify_courses` 已完成且符合條件時可能刪除 `teacher_module_courses`，本工作不重建該表。
- 本階段不整合 AI 推薦資料表、不搬移老師端 API、不製作 Vue 頁面。

## 設計原則

### Migration 是正式結構的唯一變更紀錄

所有新表與資料搬移由 `007_database_foundation` 完成。Model 描述最新版結構，Migration 描述已存在的資料庫如何安全走到最新版。

### 使用 expand-contract 避免一次破壞相依程式

`courses.reference_midi_path` 暫時保留。007 先新增 `reference_midis` 並回填資料；程式改為雙寫。等所有讀取端都改用新表後，後續 Migration 才移除舊欄位。

### 學習資料保留老師與課程邊界

`reference_midis` 與 `lesson_summaries` 都保存 `teacher_id` 與 `course_id`。`lesson_summaries` 另外保存 `student_id`，符合 ADR-0002 的資料隔離要求。

## 新資料表

### `reference_midis`

| 欄位 | 型別 | 規則 | 用途 |
| --- | --- | --- | --- |
| `id` | UUID | PK | 參考 MIDI 識別碼 |
| `course_id` | UUID | FK → `courses.id`, UNIQUE, NOT NULL | 一門課最多一份 |
| `teacher_id` | UUID | FK → `users.id`, NOT NULL | 所屬老師 |
| `storage_key` | varchar(500) | NOT NULL | 檔案儲存位置；目前為相對路徑 |
| `original_filename` | varchar(255) | NOT NULL | 使用者上傳時的檔名；舊資料由路徑檔名回填 |
| `content_sha256` | varchar(64) | NULL | 新上傳檔案的 SHA-256；舊資料無法可靠還原時為空 |
| `file_size_bytes` | bigint | NULL, >= 0 | 新上傳檔案大小 |
| `created_at` | timestamptz | NOT NULL | 建立時間 |
| `updated_at` | timestamptz | NOT NULL | 最後更新時間 |

索引：`teacher_id, course_id`。刪除課程時，由 FK cascade 刪除 metadata；實體檔案清理留給後續儲存服務處理。

### `lesson_summaries`

| 欄位 | 型別 | 規則 | 用途 |
| --- | --- | --- | --- |
| `id` | UUID | PK | 摘要識別碼 |
| `lesson_session_id` | UUID | FK → `lesson_sessions.id`, UNIQUE, NOT NULL | 即將上課的正式課堂 |
| `previous_lesson_session_id` | UUID | FK → `lesson_sessions.id`, NULL | 前一堂正式課堂 |
| `course_id` | UUID | FK → `courses.id`, NOT NULL | 所屬課程 |
| `teacher_id` | UUID | FK → `users.id`, NOT NULL | 所屬老師 |
| `student_id` | UUID | FK → `users.id`, NOT NULL | 所屬學生 |
| `window_started_at` | timestamptz | NULL | 前一堂結束時間；沒有前一堂時可空 |
| `window_ended_at` | timestamptz | NOT NULL | 本堂開始時間 |
| `source_recording_count` | integer | NOT NULL, >= 0 | 本摘要使用的錄音數 |
| `summary_text` | text | NULL | 課前摘要內容 |
| `status` | varchar(32) | pending/completed/failed | 產生狀態 |
| `generated_at` | timestamptz | NULL | 完成產生時間 |
| `created_at` | timestamptz | NOT NULL | 建立時間 |
| `updated_at` | timestamptz | NOT NULL | 最後更新時間 |

時間約束：`window_started_at` 為空，或 `window_ended_at > window_started_at`。

索引：`teacher_id, course_id, student_id` 及 `course_id, student_id, window_ended_at`。

## 既有 MIDI 資料搬移

007 升級時查詢 `courses.reference_midi_path IS NOT NULL` 的課程，為每門課建立一筆 `reference_midis`：

- `storage_key` 使用原路徑。
- `original_filename` 使用路徑最後一段。
- `teacher_id` 使用課程的老師。
- `content_sha256`、`file_size_bytes` 保持 NULL，因資料庫不能假設部署主機仍持有檔案。

007 降級時只刪除新表，不修改 `courses.reference_midi_path`，避免降級造成既有路徑遺失。

## 程式行為

建立課程並上傳 MIDI 時：

1. 驗證檔案非空，副檔名為 `.mid` 或 `.midi`。
2. 將檔案寫入目前的 `uploads/midi/<teacher_id>/`。
3. 建立 `courses`，過渡期保留 `reference_midi_path`。
4. 建立 `reference_midis`，保存 storage key、原始檔名、SHA-256 與檔案大小。
5. 同一個資料庫 transaction 提交兩筆資料。
6. 若資料庫提交失敗，刪除本次剛寫入的檔案，避免孤兒檔案。

## 測試邊界

### Alembic 公開邊界

使用名稱以 `_test` 結尾的獨立 PostgreSQL：

- 升到 `006_message_client_id`。
- 建立含 `reference_midi_path` 的既有課程。
- 升到 head。
- 驗證兩張新表、約束、索引與 MIDI 回填。
- 降回 `006_message_client_id`，驗證新表移除且舊路徑仍在。

### Service 公開邊界

呼叫 `create_course(...)` 並提供 MIDI：

- 同時建立 `courses` 與 `reference_midis`。
- 新舊路徑一致。
- SHA-256、大小、原始檔名正確。
- 非 MIDI 副檔名被拒絕。

## 非目標

- 不產生課前摘要文字。
- 不把錄音評分接入課前摘要。
- 不統一老師端舊 API。
- 本工作不新增移除 `teacher_module_courses` 的操作；是否已由上游 005 移除取決於既有資料狀態。
- 不移除 `courses.reference_midi_path`。
- 不移除 `Base.metadata.create_all()`。
- 不整合 `feature/AICourseFinder` 的資料表或 Next.js。

## 後續工作

1. 老師端與學生端統一使用 `courses`。
2. 將 MIDI 讀取端改用 `reference_midis`。
3. 移除舊 `reference_midi_path`。
4. 補上課前摘要產生及時間範圍查詢。
5. 將 AI 推薦連到正式課程資料。
6. 所有正式表都有 Migration 後移除 `create_all()`。
