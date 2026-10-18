# 資料庫過渡整合設計

## 目的

以 `origin/feature/backend` 的 Alembic 009 與正式課程模型為基底，移植資料庫基礎分支中仍有價值的參考 MIDI metadata。整合後維持單一 Alembic head，並讓現有 MIDI 下載、練習評分與課前摘要不需同時改寫。

## 範圍

- 新增 `010_reference_midis`，接在 `009_images_profile` 後。
- 新增一門課最多一筆的 `reference_midis` metadata。
- 由 `courses.reference_midi_path` 回填既有 MIDI。
- 上傳或更換 MIDI 時，同一交易同步更新舊欄位與 metadata。
- 保留 `courses.reference_midi_path` 作為過渡期讀取來源。
- 沿用既有 `lesson_preparation_summaries`，不建立第二套課前摘要表。
- 補 Migration、API 整合與 metadata 註冊測試。
- 更新資料字典與 Migration 維運說明。

## 非目標

- 本階段不把檔案移到 S3 或 MinIO。
- 本階段不刪除 `courses.reference_midi_path`。
- 本階段不修改練習評分或課前摘要演算法。
- 本階段不整合 AICourseFinder。

## 資料結構

`reference_midis` 保存：

- UUID 主鍵。
- 課程與老師外鍵。
- 目前檔案的 `storage_key` 與上傳時檔名。
- SHA-256 與檔案大小。
- 建立與更新時間。

課程刪除時 metadata 由資料庫連動刪除；課程目前採封存而非實體刪除，所以一般操作不會觸發這條規則。

## 過渡策略

Migration 先建立 metadata 表並回填舊路徑。應用程式上傳新 MIDI 時同時更新 `courses.reference_midi_path` 與 `reference_midis`。現有讀取端繼續讀舊欄位；待所有讀取端改用 metadata 後，另開 Migration 移除舊欄位。

## 失敗處理

新檔案先寫入檔案系統，再在同一資料庫交易寫入課程與 metadata。資料庫提交失敗時 rollback，並刪除這次新寫入的檔案。先前版本的 MIDI 仍保留，讓已評分錄音可追溯當時使用的曲子。

## 驗收

1. 全新 PostgreSQL 可由 001 升級到 010，且只有一個 Alembic head。
2. 009 中非空白的舊 MIDI 路徑會回填一筆 metadata。
3. 010 降回 009 時，舊路徑仍存在。
4. API 上傳 MIDI 後，舊欄位與 metadata 指向同一路徑。
5. 更換 MIDI 只更新同一門課的 metadata，不新增第二筆。
6. 非 MIDI、空檔與超過大小限制的檔案不建立 metadata。
