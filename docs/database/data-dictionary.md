# 資料庫資料字典

這份文件說明目前正式 PostgreSQL 結構中，與 Issue #18 資料基礎直接相關的資料。欄位的最終真相以 Alembic Migration 為準；SQLAlchemy Model 是應用程式操作這些資料時使用的 Python 對照表。

## 小白版心智模型

資料從網頁進入資料庫時，大致經過四層：

1. FastAPI Router 接收表單或 API 請求。
2. Service 驗證規則，例如課程名稱不能空白、檔案必須是 MIDI。
3. SQLAlchemy Model 把 Python 物件轉成 SQL。
4. PostgreSQL 把資料真正保存到資料表，並執行外鍵、唯一值和檢查約束。

`backend/models/*.py` 像是「最新版資料表的 Python 說明書」。`alembic/versions/*.py` 像是「資料庫裝修紀錄」，負責把已存在的資料庫一步一步改到最新版。正式環境不能只改 Model，也不能只靠 `Base.metadata.create_all()`。

## Migration 版本鏈

```text
001 users
  → 002 teacher applications / auth identities
  → 003 optional teacher proof
  → 004 student learning
  → 005 unify courses
  → 006 message client id
  → 007 reference MIDI / lesson summaries
```

007 採 expand-contract：先新增正式 metadata 表、回填舊資料並讓程式雙寫；等所有讀取端都完成搬移後，未來版本才能移除 `courses.reference_midi_path`。

## `reference_midis`：參考 MIDI

資料庫只保存檔案的 metadata。MIDI 內容目前仍放在應用程式主機的檔案系統。

| 欄位 | 可空 | 說明 |
| --- | --- | --- |
| `id` | 否 | UUID 主鍵 |
| `course_id` | 否 | 所屬課程；一門課最多一筆，刪除課程時 metadata 一起刪除 |
| `teacher_id` | 否 | 所屬老師 |
| `storage_key` | 否 | 目前存放檔案的路徑 |
| `original_filename` | 否 | 上傳時的檔名；舊資料由既有路徑推得 |
| `content_sha256` | 是 | 新上傳內容的 SHA-256，可用來核對檔案完整性；舊資料可能沒有 |
| `file_size_bytes` | 是 | 新上傳內容的位元組數；舊資料可能沒有 |
| `created_at` | 否 | 建立時間 |
| `updated_at` | 否 | metadata 最後更新時間 |

約束與索引：

- `uq_reference_midis_course_id`：一門課最多一份參考 MIDI。
- `ck_reference_midis_file_size_nonnegative`：檔案大小不能是負數。
- `fk_reference_midis_course_id_courses`：課程必須存在，課程刪除時連動刪除 metadata。
- `fk_reference_midis_teacher_id_users`：老師帳號必須存在。
- `ix_reference_midis_teacher_course`：加速依老師及課程查詢。

過渡期規則：

- 新上傳會同時寫入 `courses.reference_midi_path` 和 `reference_midis.storage_key`。
- 007 會把非 NULL 的舊路徑回填到新表。
- 007 降級不會清除 `courses.reference_midi_path`。
- 刪除 metadata 不會自動刪除磁碟上的檔案；檔案生命週期服務是後續工作。

## `lesson_summaries`：課前摘要

一筆資料代表「某位學生某堂即將上課的正式課堂」所使用的課前摘要。它與單次錄音的 `practice_feedbacks` 分開保存，符合 ADR-0001。

| 欄位 | 可空 | 說明 |
| --- | --- | --- |
| `id` | 否 | UUID 主鍵 |
| `lesson_session_id` | 否 | 摘要要提供給哪一堂課；每堂最多一筆 |
| `previous_lesson_session_id` | 是 | 前一堂正式課堂；第一堂可為空 |
| `course_id` | 否 | 所屬課程 |
| `teacher_id` | 否 | 所屬老師 |
| `student_id` | 否 | 所屬學生 |
| `window_started_at` | 是 | 蒐集練習資料的開始時間；第一堂可為空 |
| `window_ended_at` | 否 | 蒐集區間結束時間，通常是本堂開始時間 |
| `source_recording_count` | 否 | 本摘要使用的練習錄音數，預設 0 |
| `summary_text` | 是 | 課前摘要內容；尚未完成或失敗時可為空 |
| `status` | 否 | `pending`、`completed` 或 `failed` |
| `generated_at` | 是 | 摘要完成產生的時間 |
| `created_at` | 否 | 建立時間 |
| `updated_at` | 否 | 最後更新時間 |

約束與索引：

- `uq_lesson_summaries_lesson_session_id`：一堂正式課堂最多一份摘要。
- `ck_lesson_summaries_source_count_nonnegative`：來源錄音數不能是負數。
- `ck_lesson_summaries_status`：狀態只能使用定義好的三種值。
- `ck_lesson_summaries_window_order`：有開始時間時，結束時間必須比較晚。
- 五個具名外鍵確保課堂、前一堂課、課程、老師和學生都存在。
- `ix_lesson_summaries_teacher_course_student`：加速依資料歸屬查詢。
- `ix_lesson_summaries_course_student_window_end`：加速依課程、學生及時間區間查詢。

007 只建立保存結構，尚未決定如何認定一堂課「已完成」，也尚未產生摘要文字。這些規則要在摘要產生功能開始前，以 ADR 明確定義。

## 相關既有資料

| 資料表 | 用途 | 與本階段的關係 |
| --- | --- | --- |
| `users` | 老師、學生、管理者帳號 | 新表的老師與學生外鍵來源 |
| `courses` | 正式課程 | 參考 MIDI 與課前摘要的課程來源 |
| `lesson_sessions` | 已排定的正式課堂 | 課前摘要的目標課堂與前一堂課來源 |
| `practice_recordings` | 學生每次練習錄音 | 未來摘要的來源資料之一 |
| `practice_feedbacks` | 單次錄音分析結果 | 保持單次回饋，不取代課前摘要 |

## 目前已知的資料治理待辦

1. 定義完成課堂的正式狀態或判定規則，並新增 ADR。
2. 把所有參考 MIDI 讀取端改用 `reference_midis`，之後移除舊欄位。
3. 把檔案移到具備版本、權限、備份及生命週期政策的物件儲存服務。
4. 建立自動備份、還原演練、監控、資料保留和個資刪除政策。
5. 用複合約束或資料庫 trigger 強化老師、學生、課程與課堂的歸屬一致性。
