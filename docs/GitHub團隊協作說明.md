# GitHub 團隊協作說明

| 項目 | 內容 |
| --- | --- |
| 適用專案 | AIPE04_group3 |
| 最後更新 | 2026-11-01 |

## 1. 核心規則

1. 不直接在 `main` 寫程式。
2. `main` 是唯一長期正式主線；每次新功能都從最新 `main` 建立新分支。
3. 只在這次工作的功能分支修改，不順手改無關的模組。
4. 不要動到別人的程式碼與未提交內容。
5. `.env`、API Key、Password、Token、真實個資與錄音不可 Push。
6. 功能完成後開 Pull Request，經 Review 與 CI 通過後合併。

完整架構、資料來源、開發步驟與驗收標準以 `docs/專案架構與開發驗證手冊.md` 為準。CI 檢查項目見 `docs/ci-and-pr.md`。舊 `feature/AICourseFinder` 只作研究參考，未來正式搜尋與 RAG 不在該分支繼續開發。

## 2. 分支

每次工作都從最新 `main` 建立分支，用名稱說明這次做什麼，例如 `feature/course-search-v1`、`docs/update-project-docs`。合併後就不再使用。遠端舊有的 `feature/backend`、`feature/frontend` 不是長期開發基地。

## 3. 第一次加入

```bash
git clone <GitHub 專案網址>
cd AIPE04_group3
git branch -a
git switch -c feature/這次的功能 origin/main
git branch --show-current
```

若要接續遠端已有的分支：

```bash
git switch --track origin/feature/這次的功能
```

## 4. 每天開始

```bash
git status
git branch --show-current
git fetch origin
```

若要同步 `main`：

```bash
git switch main
git pull origin main
git switch feature/這次的功能
git merge main
```

發生衝突時先確認每一段的來源與用意；不確定就停止並詢問，不要直接選「全部採用目前版本」。

## 5. 開發完成

先查看變更：

```bash
git status
git diff
```

只加入本次相關檔案：

```bash
git add <本次修改的檔案>
git status
```

Commit 與 Push：

```bash
git commit -m "用繁體中文說明實際完成內容"
git push -u origin feature/這次的功能
```

不要無腦使用 `git add .`，避免把 `.env`、錄音、測試教材或其他人的修改一起送出。

## 6. Pull Request

PR 內容至少包含：

```text
## 做了什麼
- ...

## 影響範圍
- API：無／...
- Database：無／Migration ...
- Frontend：無／...
- Environment：無／新增 ...

## 驗證
- 執行 ...，結果 ...

## 需要 Reviewer 注意
- 權限、共用檔案、已知限制或待串接項目
```

Reviewer 檢查：

- 是否超出這次 PR 說明的範圍。
- 是否改到共用 API／Schema。
- 是否具角色、租戶與對話權限驗證。
- 是否含 Migration 與測試。
- 是否提交 Secret、測試個資、大型音訊或教材。
- 文件是否需要同步。

## 7. 合併原則

- 任何人都不直接在 `main` 開發。
- 使用 GitHub PR 合併，保留 Review 與 CI 紀錄。
- PR 未通過測試、文件不一致或存在未解決衝突時不合併。
- 合併後通知其他分支同步 `main`。

## 8. Commit 範例

正確：

```text
新增接洽對話訊息分頁與未讀數 API
修正學生可讀取其他對話的權限漏洞
建立工作室資料表 Migration
```

避免：

```text
update
fix
完成
測試
改一下
```

## 9. 禁止指令與行為

- `git reset --hard`
- `git push --force`
- 直接刪除他人分支
- 未確認就解決他人程式衝突
- 未經要求讓 Agent 自動 Commit、Push、開 PR 或 Merge
- 將 `.env`、憑證、個資、聊天匯出、教材或錄音提交 Git

## 10. 最簡流程

```text
確認分支與狀態
→ 同步 main
→ 只修改這次相關的模組
→ 執行測試
→ 檢查 diff
→ 中文 Commit
→ Push 功能分支
→ 開 PR
→ Review 與 CI 通過
→ 合併 main
```

