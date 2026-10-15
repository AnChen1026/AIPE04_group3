# backend

一次請求照這個順序走：`routers` 接到網址，`services` 檢查規則，`repositories` 讀寫資料，`models` 對應資料表。

專案唯一正式啟動入口是根目錄的 `app.py`。老師端檔案已依用途放回下列共用分層，不再使用 `backend/teacher/`。

| 資料夾 | 放什麼 |
| --- | --- |
| `routers` | 網址與函式的對應。接收表單或 JSON，再把結果回給瀏覽器 |
| `schemas` | 進來和出去的資料格式，例如註冊要有哪些欄位 |
| `services` | 業務規則，例如密碼對不對、老師能不能核准 |
| `repositories` | 資料庫的查詢與寫入。這裡不判斷業務對錯 |
| `models` | 資料表的形狀。一個 class 對應一張表 |
| `dependencies` | Route 共用的登入、角色與老師身分檢查 |
| `core` | 全站共用設定，例如讀 `.env`、連線資料庫、密碼雜湊與上傳路徑 |

新功能在這幾個資料夾各加檔案。不要把 SQL 直接寫在 `routers`。

老師端 Route 使用 `backend/routers/teacher_*.py`；資料同步集中在 `backend/services/teacher_sync.py`，檔案上傳路徑集中在 `backend/core/uploads.py`。
