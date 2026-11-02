# 鋼琴課程與教師名單重編 Implementation Plan

> **For agentic workers:** Execute the tasks sequentially in this session; preserve existing catalog identities and validate each deliverable.

**Goal:** 用有實質差異的鋼琴課與相符教師介紹取代重複的 426 筆示範課程，補齊進階檢索。

**Architecture:** 以公開教學資料研究建立編輯主題庫，產出固定、可檢查的課程 JSON。教師與課程 ID 不變；更新只接受已知舊版或新版內容，並同步重建 staging 語意索引。

**Tech Stack:** Python、JSON、SQLAlchemy、pytest、既有 embedding gateway。

**Spec:** 使用者要求廣泛搜尋後重編教師名單與課程內容，解決程度缺漏、關鍵字與詳細介紹重複。

## Global Constraints

- 保留 426 個課程 ID 及原有師生關聯；不建立真實老師身分或學經歷。
- 四個程度各至少 80 門，進階須有具體先備能力。
- 課名全部唯一；每個核心主題最多 6 門，內容需有不同練習任務。
- 介紹包含適合對象、先備能力、具體內容、練習與成果、授課安排。
- 不把來源網址、假資料標記或索引維護資訊放進公開課程文案。

## Review Focus

- 只換課名但正文仍重複：檢查標題與教學內容唯一性、近似度和主題分布。
- 進階只改標籤：查核複音、曲式、進階即興、合作演奏等先備要求與課綱。
- 老師同時教授互不相干的專業：同一老師的課程放在同一核心領域並同步專長。
- 更新覆寫人工修改：只允許比對已知版本的課名、內容指紋與目錄欄位。
- 文字改了但檢索未生效：核對 staging 正式欄位與 embedding content hash。

### Task 1: 研究與重編

**Files:** `scripts/data/piano-curriculum.json`、`scripts/build_demo_catalog.py`、`scripts/data/aicourse-demo.json`、`docs/piano-catalog-research.md`

- [x] 記錄第一手公開課程來源與採用的主題方向。
- [x] 建立分級課綱，每個核心主題有不同子題、任務及成果；同一老師搭配相近課程。
- [x] 產出 426 個唯一課名與有實質差異的介紹，補齊教師專長和教法。
- [x] 產出分布與相似度報告，抽查跨程度、跨領域課程。

### Task 2: 安全更新既有目錄

**Files:** `scripts/import_demo_data.py`、`tests/test_demo_import.py`、`tests/catalog/test_catalog_content.py`

- [x] 增加已知舊版資料更新、拒絕人工改動、重複執行與新增資料測試。
- [x] 更新課名、程度、風格、介紹及相符教師資料，保留 ID 與其他使用者資料。
- [x] 執行隔離測試與內容品質檢查。

### Task 3: 套用與驗收

- [x] staging dry-run 通過後套用更新，核對 426 筆欄位與教師關聯。
- [x] 重建索引並核對沒有過期的 content hash。
- [x] 直接 commit / push 至 main（沿用使用者本次工作先前指示），回報數據與限制。
