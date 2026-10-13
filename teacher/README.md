# 教師端拆分

從包含 `teacher/` 與 `backend/` 的共同專案根目錄執行：

模板預設位於專案根目錄 `templates/fastapi_teacher_test.html`。上傳資料夾預設位於專案根目錄 `uploads/`。

- `main.py`：建立 app、middleware、router 與開發用建表。
- `models/`：資料庫 ORM 模型。
- `schemas/`：Pydantic 請求格式。
- `routers/`：依功能拆分 API，原路徑不變。
- `dependencies/teacher.py`：登入教師與審核驗證。
- `services/teacher_sync.py`：共用 User 同步教師 profile 的事件。
- `core/uploads.py`：上傳目錄。

