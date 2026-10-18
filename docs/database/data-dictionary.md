# 資料庫資料字典

## 小白版心智模型

資料由網頁進入 PostgreSQL 時，依序經過：

1. FastAPI Router 接收請求。
2. Service 驗證權限與商業規則。
3. SQLAlchemy Model 把 Python 物件轉成 SQL。
4. PostgreSQL 保存資料並執行外鍵、唯一值與檢查限制。

`backend/models/*.py` 是目前資料表的 Python 對照；`alembic/versions/*.py` 是資料庫從舊版走到新版的正式紀錄。所有正式資料表由 Alembic 建立，應用程式啟動時不使用 `create_all()`。

## Migration 版本鏈

```text
001 users
  → 002 teacher applications / auth identities
  → 003 optional teacher proof
  → 004 student learning
  → 005 unify courses
  → 006 message client id
  → 007 teacher tables
  → 008 lesson preparation summaries
  → 009 images / optional teacher profile
  → 010 reference MIDI metadata
```

目前只有一個 head：`010_reference_midis`。

## `courses` 與參考 MIDI

`courses` 是課程的權威資料表。每門課只能由自己的老師管理，狀態為 `draft`、`published` 或 `archived`；只有 `published` 可以公開顯示及建立接洽。

過渡期間，`courses.reference_midi_path` 繼續供現有下載、評分與摘要功能讀取。新的上傳同時寫入這個欄位及 `reference_midis`。

## `reference_midis`

一筆代表一門課目前使用的參考 MIDI。資料庫保存 metadata，MIDI 內容目前仍放在應用程式主機的 `uploads/midi/`。

| 欄位 | 可空 | 說明 |
| --- | --- | --- |
| `id` | 否 | UUID 主鍵 |
| `course_id` | 否 | 所屬課程；一門課最多一筆 |
| `teacher_id` | 否 | 所屬老師帳號 |
| `storage_key` | 否 | 檔案儲存位置 |
| `original_filename` | 否 | 上傳時的安全檔名 |
| `content_sha256` | 是 | 檔案內容 SHA-256；舊資料回填時可能沒有 |
| `file_size_bytes` | 是 | 檔案大小；舊資料回填時可能沒有 |
| `created_at` | 否 | metadata 建立時間 |
| `updated_at` | 否 | metadata 最後更新時間 |

約束與索引：

- `uq_reference_midis_course_id`：一門課只有一筆目前版本。
- `ck_reference_midis_file_size_nonnegative`：檔案大小不能是負數。
- `fk_reference_midis_course_id_courses`：課程不存在時不能建立；實體刪除課程會連動刪除 metadata。
- `fk_reference_midis_teacher_id_users`：老師帳號必須存在。
- `ix_reference_midis_teacher_course`：加速老師依課程查詢。

過渡規則：

- 010 會回填非空白的 `courses.reference_midi_path`。
- 舊資料沒有原始內容可重新計算，因此 SHA-256 與大小可以是 NULL。
- 新上傳會計算 SHA-256、大小並同步更新新舊兩處。
- 更換 MIDI 更新同一筆 metadata；舊檔案暫時保留，讓已評分錄音仍可追溯原曲。
- 010 降級只刪除 metadata 表，不清除舊路徑。

## `lesson_preparation_summaries`

課前摘要沿用 Alembic 008 建立的 `lesson_preparation_summaries`。一筆摘要只屬於一堂正式課、同一位老師、同一門課與同一位學生。來源範圍為上一堂結束到這一堂開始；沒有平台紀錄時必須明確說明，不推論成學生沒有練習。

本次整合不建立第二套 `lesson_summaries`。

## 後續 Contract 階段

只有在下列條件都完成後，才能移除 `courses.reference_midi_path`：

1. 老師與學生下載端改讀 `reference_midis.storage_key`。
2. 新練習錄音能固定記住當次使用的 MIDI 版本或不可變 storage key。
3. 音訊評分與課前摘要不再讀舊欄位。
4. 正式資料完成筆數與路徑比對。
5. 已完成備份及還原演練。

## 資料治理待辦

- 將 MIDI、錄音與圖片移到具備權限、版本、備份及生命週期政策的物件儲存。
- 建立每日自動備份、跨主機保存與定期還原演練。
- 分開應用程式、Migration 與唯讀分析帳號。
- 定義個資保存期限、使用者刪除與操作稽核政策。
- 在後續 Migration 強化老師、課程與學生的複合歸屬一致性。

