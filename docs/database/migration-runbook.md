# Alembic Migration 維運手冊

## 團隊規則

1. 已在共享環境執行過的 Migration 不可修改；修正時新增下一版。
2. Model、Migration、資料搬移、測試與資料字典放在同一個 PR。
3. 合併前確認 `alembic heads` 只有一個 head。
4. 刪欄位、改型別、重建索引與大量回填前先備份，並用接近正式資料量的副本計時。
5. 不在正式資料庫手動建表或修改 `alembic_version`。

## 日常檢查

```bash
alembic current
alembic heads
alembic history --verbose
```

預期 head：

```text
010_reference_midis (head)
```

建立新版本前，先同步主分支並確認目前 head。新 Migration 的 `down_revision` 必須指向當下唯一 head。

## 本機升級

`.env` 設定本機 PostgreSQL 後執行：

```bash
alembic upgrade head
```

應用程式不再執行 `Base.metadata.create_all()`；缺少 Migration 時，啟動網站不會替你補表。

## Migration 整合測試

破壞性測試只能使用名稱以 `_test` 結尾的獨立 PostgreSQL：

```bash
TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/project_test \
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/project_test \
pytest tests/database -q
```

測試會清除測試資料庫的 `public` schema。不得把正式、開發共用或含重要資料的 URL 放進 `TEST_DATABASE_URL`；fixture 會拒絕非 PostgreSQL 及名稱不是 `_test` 的資料庫。

## 010 上線前檢查

檢查需要回填的課程數：

```sql
SELECT COUNT(*)
FROM courses
WHERE NULLIF(btrim(reference_midi_path), '') IS NOT NULL;
```

升級後檢查 metadata 數量及漏接資料：

```sql
SELECT COUNT(*) FROM reference_midis;

SELECT c.id, c.reference_midi_path
FROM courses AS c
LEFT JOIN reference_midis AS r ON r.course_id = c.id
WHERE NULLIF(btrim(c.reference_midi_path), '') IS NOT NULL
  AND r.id IS NULL;
```

第二個查詢預期回傳 0 筆。

## 備份與還原演練

上線前由有權限的操作人員建立 custom-format 備份：

```bash
pg_dump --format=custom --file=backup-before-migration.dump DATABASE_NAME
```

備份完成不代表可以還原。團隊應定期在隔離資料庫執行：

```bash
createdb restore_drill
pg_restore --dbname=restore_drill backup-before-migration.dump
```

並記錄備份時間、檔案大小、保存位置、還原耗時及抽查結果。正式環境應使用受控帳號與秘密管理，不把密碼寫進命令、文件或 Git。

## 部署順序

1. 確認應用程式版本與唯一 Migration head。
2. 建立備份並確認最近一次還原演練有效。
3. 暫停會與結構變更衝突的背景工作。
4. 執行 `alembic upgrade head`。
5. 執行 010 的回填檢查 SQL。
6. 部署同版本 FastAPI。
7. 測試登入、課程列表、MIDI 上傳／下載及練習送出。
8. 觀察錯誤率、資料庫連線、transaction rollback、磁碟與備份狀態。

## Rollback 原則

010 可執行：

```bash
alembic downgrade 009_images_profile
```

這會刪除 `reference_midis`，但保留 `courses.reference_midi_path`，所以舊版下載與評分仍能使用。降級前仍要備份；新上傳的 SHA-256、原始檔名與大小只存在 metadata，降級後會失去。

資料已大量寫入、後續版本已依賴新表或事故原因不明時，優先新增向前修正的 Migration，不要直接降級或手動刪表。

## 事故處理

Migration 失敗時停止繼續部署與寫入，保存 FastAPI、Alembic 與 PostgreSQL log，記錄應用程式 commit、`alembic current`、失敗 SQL 和發生時間。依交易是否 rollback、資料是否已寫入及備份能否還原，決定向前修正或還原。
