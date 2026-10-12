# GitHub 團隊協作說明

| 項目 | 內容 |
| --- | --- |
| 版本 | V1.2 |
| 適用專案 | AIPE04_group3 |
| 最後更新 | 2026-09-24 |

## 1. 核心規則

1. 不直接在 `main` 寫程式。
2. 只在自己的功能分支修改自己負責的模組。
3. 不要動到別人的程式碼與未提交內容。
4. `.env`、API Key、Password、Token、真實個資與錄音不可 Push。
5. 功能完成後開 Pull Request，由組長或指定 Reviewer 合併。

## 2. 分支

以 2026-10-12 分工為準。

| 負責人 | 負責範圍 | 建議分支 |
| --- | --- | --- |
| 姿彣 | UI/UX | 依該次介面工作指定 |
| Ken | 前端 | 依該次前端工作指定 |
| 禹銨 | 後端與語音 | `feature/login`、`feature/backend`、`feature/ai-practice` |
| 宇鈞 | Review | 依該次審查指定 |
| 雄 | DevOps | 依該次部署工作指定 |
| Ollie | 資料庫與 AI | `feature/database`、`feature/ai-support` |
| 永富 | AI 測驗題目生成 | `feature/ai-quiz` |

接洽對話的畫面由姿彣與 Ken 負責，API 由禹銨負責。不要把 `feature/messaging` 當成已指定的負責人分支。永富本輪沒有實作工單。

## 3. 第一次加入

```bash
git clone <GitHub 專案網址>
cd AIPE04_group3
git branch -a
git switch feature/自己的功能
git branch --show-current
```

若遠端已有分支但本機沒有：

```bash
git switch --track origin/feature/自己的功能
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
git switch feature/自己的功能
git merge main
```

發生衝突時先確認每一段屬於誰；不確定就停止並詢問，不要直接選「全部採用目前版本」。

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
git push -u origin feature/自己的功能
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

- 是否超出負責範圍。
- 是否改到共用 API／Schema。
- 是否具角色、租戶與對話權限驗證。
- 是否含 Migration 與測試。
- 是否提交 Secret、測試個資、大型音訊或教材。
- 文件是否需要同步。

## 7. 組長合併原則

- 組長也不建議直接在 `main` 開發。
- 使用 GitHub PR 合併，保留 Review 與 CI 紀錄。
- PR 未通過測試、文件不一致或存在未解決衝突時不合併。
- 合併後通知其他分支同步 `main`。

## 8. Commit 範例

正確：

```text
新增站內聊天訊息分頁與未讀數 API
修正學生可讀取其他對話的權限漏洞
建立測驗與題目資料表 Migration
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
→ 只修改自己的模組
→ 執行測試
→ 檢查 diff
→ 中文 Commit
→ Push 功能分支
→ 開 PR
→ Review 與 CI 通過
→ 由組長合併 main
```

