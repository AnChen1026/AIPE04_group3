# Alembic Migration 維運手冊

這份手冊供資料庫維護人員在本機、測試、預備及正式環境變更 PostgreSQL 結構。範例中的帳號、密碼和主機都必須改用環境變數或秘密管理服務，不能提交到 Git。

## 不可違反的規則

1. 已經在共享環境執行過的 Migration 不可修改；修正要新增下一版。
2. Model 變更與 Migration 必須在同一個 PR，並說明資料如何回填及如何降級。
3. 不可拿開發或正式資料庫跑整合測試；測試資料庫名稱必須以 `_test` 結尾。
4. 刪欄位、改型別、重建索引及大量回填前必須備份，並先在接近正式資料量的環境計時。
5. 一次部署若同時改資料庫與程式，優先採 expand-contract，讓舊版和新版程式能短暫共存。

## 每日查看指令

```bash
uv sync --group dev
uv run alembic current
uv run alembic heads
uv run alembic history --verbose
```

正常狀態應只有一個 head。此分支的預期 head 是 `007_database_foundation`。若看到兩個 heads，先釐清分支合併順序，再建立 merge revision；不要任意把其中一個版本號改掉。

007 可單獨產生離線 SQL 供 DBA 審查：

```bash
uv run alembic upgrade 006_message_client_id:007_database_foundation --sql \
  > /tmp/aipe04-007.sql
```

目前不能從 base 一次產生完整離線 SQL，因為既有 `005_unify_courses` 會在執行時檢查資料庫現況，而離線模式沒有真實連線。線上 upgrade 已由整合測試覆蓋；若團隊需要完整靜態 SQL，應另外開工單改善 005 的部署策略，不可直接改寫已套用的 revision。

## 建立一個 Migration

1. 從最新 Migration head 建立工作分支。
2. 先寫會失敗的 PostgreSQL 整合測試。
3. 修改 SQLAlchemy Model。
4. 建立新 revision：

   ```bash
   uv run alembic revision -m "describe the schema change"
   ```

5. 人工檢查 upgrade 與 downgrade。autogenerate 只能當草稿，不能代替審查。
6. 為 constraint 和 index 使用穩定、可讀的名稱。
7. 用既有資料測試 upgrade，用升級後資料測試 downgrade。
8. 更新資料字典與部署說明。

## 本機整合測試

可以使用獨立 PostgreSQL container。以下 container 不掛永久 volume，停止後資料會刪除：

```bash
docker run -d --rm \
  --name aipe04-test-postgres \
  -e POSTGRES_USER=aipe04 \
  -e POSTGRES_PASSWORD=aipe04 \
  -e POSTGRES_DB=aipe04_test \
  -p 127.0.0.1:55433:5432 \
  postgres:16

export TEST_DATABASE_URL='postgresql+psycopg://aipe04:aipe04@127.0.0.1:55433/aipe04_test'
uv run pytest tests/database -v
```

測試 fixture 會再檢查資料庫種類與 `_test` 後綴，然後在每個測試前後執行 destructive downgrade。這道檢查不能刪除。

## 上線前備份

由有權限的操作人員建立帶時間戳的 custom-format 備份：

```bash
pg_dump --format=custom --no-owner --no-acl \
  --file="aipe04-before-<revision>-$(date +%Y%m%d-%H%M%S).dump" \
  "$DATABASE_URL"
```

備份完成不等於可還原。團隊應定期在隔離資料庫使用 `pg_restore` 演練，記錄：

- 還原所需時間（RTO）。
- 最多可接受遺失多少資料（RPO）。
- 備份保存期限、加密方式和存取人員。
- 還原後的資料筆數與關鍵查詢驗證結果。

## 部署流程

1. 確認應用程式版本、Migration head 和資料庫備份完成。
2. 在預備環境用正式資料的匿名化副本跑 upgrade。
3. 檢查鎖定時間、執行時間、磁碟使用量和慢查詢。
4. 先部署可同時讀寫新舊結構的程式。
5. 執行：

   ```bash
   uv run alembic upgrade head
   uv run alembic current
   ```

6. 執行 smoke test：登入、建立課程、上傳參考 MIDI、查詢課程。
7. 觀察錯誤率、資料庫連線、transaction rollback、磁碟及備份狀態。
8. 等所有讀取端穩定使用新結構後，才在另一個版本移除舊欄位。

## 007 專用驗證

升級後執行唯讀查詢：

```sql
SELECT version_num FROM alembic_version;

SELECT COUNT(*) AS legacy_paths
FROM courses
WHERE reference_midi_path IS NOT NULL;

SELECT COUNT(*) AS migrated_reference_midis
FROM reference_midis;

SELECT c.id
FROM courses AS c
LEFT JOIN reference_midis AS r ON r.course_id = c.id
WHERE c.reference_midi_path IS NOT NULL
  AND r.id IS NULL;
```

最後一個查詢必須回傳 0 筆。新上傳資料還要抽查 `storage_key`、`original_filename`、`content_sha256` 和 `file_size_bytes`。

## 降級與事故處理

007 可以降回 006：

```bash
uv run alembic downgrade 006_message_client_id
```

執行前要知道：

- 這會刪除整張 `lesson_summaries` 和 `reference_midis`，所以先備份。
- `courses.reference_midi_path` 會保留，因此由舊欄位回填的路徑仍存在。
- 007 上線後才新增的 hash、檔案大小及摘要資料不在舊欄位中，降級會遺失。
- 上游 `005_unify_courses` 的 downgrade 是空操作；不要把它當成可完整復原老師端舊表的工具。

事故發生時先停止繼續寫入，保留應用程式與 PostgreSQL log，記錄當時 revision 和失敗 SQL。依資料是否已寫入、是否能向前修正、是否需要還原備份來決定處理方式。不要在正式資料庫手動刪表後再猜測 Alembic 版本。

## 業界維護能力清單

資料庫主要維護人員應逐步補齊：

- 每日自動備份、跨主機保存及定期還原演練。
- 最小權限帳號：應用程式帳號、Migration 帳號、唯讀分析帳號分開。
- 連線數、CPU、記憶體、磁碟、鎖等待、慢查詢和 replication lag 監控。
- schema 變更 PR 範本、雙人審查和部署紀錄。
- 個資盤點、保留期限、刪除流程及稽核 log。
- 大表 online migration 策略，例如分批回填與 `CREATE INDEX CONCURRENTLY`。
- 容量預估、索引使用率檢查、`VACUUM`/`ANALYZE` 與 PostgreSQL 升級計畫。
