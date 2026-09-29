# 個人工作室智慧管理平台 API 規格

| 項目 | 內容 |
| --- | --- |
| 版本 | V1.2 Draft |
| Base Path | `/api/v1` |
| 最後更新 | 2026-09-24 |

> 本文件定義建議 Contract。實作前需對照 Repository 既有 Endpoint；若不同，先列差異並由團隊確認，避免 Breaking Change。

## 1. 共通規則

- JSON 使用 UTF-8，欄位採 `snake_case`。
- 時間使用 ISO 8601 含時區，例如 `2026-09-24T10:00:00+08:00`。
- 列表使用 `limit` 與 `cursor`；預設 `limit=20`，上限 100。
- 修改操作可使用 `Idempotency-Key` Header。
- 高併發資源以 `version` 或 `If-Match` 防止覆蓋。

成功：

```json
{
  "data": {},
  "meta": {"request_id": "..."}
}
```

失敗：

```json
{
  "error": {
    "code": "SCHEDULE_CONFLICT",
    "message": "所選時段目前無法使用",
    "details": []
  },
  "meta": {"request_id": "..."}
}
```

## 2. Auth

| Method | Path | 權限 | 說明 |
| --- | --- | --- | --- |
| POST | `/auth/register` | Public | 註冊 teacher 或 student |
| POST | `/auth/login` | Public | 登入 |
| POST | `/auth/logout` | Login | 登出／撤銷 Session |
| GET | `/auth/me` | Login | 目前帳號與固定角色 |
| POST | `/auth/password/forgot` | Public | 申請重設 |
| POST | `/auth/password/reset` | Public | 使用限時憑證重設 |

註冊 Request：

```json
{
  "email": "user@example.com",
  "password": "********",
  "role": "student",
  "display_name": "使用者"
}
```

## 3. 公開課程與推薦

| Method | Path | 權限 | 說明 |
| --- | --- | --- | --- |
| GET | `/public/courses` | Public | 搜尋／篩選有效課程 |
| GET | `/public/courses/{course_id}` | Public | 課程詳情 |
| POST | `/recommendations/sessions` | Public／Login | 建立推薦對談 |
| POST | `/recommendations/sessions/{id}/messages` | Public／Owner | 傳送需求或回答 |
| GET | `/recommendations/sessions/{id}/results` | Owner | 取得推薦結果 |
| POST | `/ai/qa` | Public／Login | 平台 QA |

AI 結構化條件示意：

```json
{
  "category": "piano",
  "learning_goal": "流行歌伴奏",
  "assessed_level": "beginner",
  "level_confidence": 0.72,
  "budget": {"min": null, "max": 1200},
  "missing_important_fields": ["available_time"]
}
```

## 4. 老師課程管理

| Method | Path | 權限 | 說明 |
| --- | --- | --- | --- |
| GET | `/teacher/courses` | Teacher | 自己工作室課程 |
| POST | `/teacher/courses` | Teacher | 建立課程 |
| GET | `/teacher/courses/{id}` | Teacher | 課程詳情 |
| PATCH | `/teacher/courses/{id}` | Teacher | 更新課程 |
| POST | `/teacher/courses/{id}/publish` | Teacher | 發布 |
| POST | `/teacher/courses/{id}/archive` | Teacher | 下架 |

## 5. 洽詢、邀請與師生關係

| Method | Path | 權限 | 說明 |
| --- | --- | --- | --- |
| POST | `/student/course-inquiries` | Student | 送出洽詢 |
| GET | `/teacher/course-inquiries` | Teacher | 待處理洽詢 |
| POST | `/teacher/course-inquiries/{id}/accept` | Teacher | 接受並建立關係 |
| POST | `/teacher/course-inquiries/{id}/reject` | Teacher | 拒絕 |
| POST | `/teacher/student-invitations` | Teacher | 建立邀請 |
| GET | `/student/invitations/preview` | Student | 預覽邀請 |
| POST | `/student/invitations/accept` | Student | 接受邀請並建立關係 |
| POST | `/teacher/student-invitations/{id}/revoke` | Teacher | 撤銷 |
| GET | `/teacher/students` | Teacher | 有效學生 |
| GET | `/student/teachers` | Student | 有效老師／課程 |

接受邀請 Request：

```json
{"code": "使用者輸入的原始邀請碼"}
```

後端不得回傳或保存原始邀請碼。

## 6. 課表與異動

| Method | Path | 權限 | 說明 |
| --- | --- | --- | --- |
| GET | `/teacher/lessons` | Teacher | 工作室課表 |
| POST | `/teacher/lessons` | Teacher | 建立課堂 |
| GET | `/student/lessons` | Student | 自己課表 |
| POST | `/student/schedule-change-requests` | Student | 提出請假／調課 |
| GET | `/teacher/schedule-change-requests` | Teacher | 待處理申請 |
| POST | `/teacher/schedule-change-requests/{id}/approve` | Teacher | 核准並嘗試執行 |
| POST | `/teacher/schedule-change-requests/{id}/reject` | Teacher | 拒絕 |
| POST | `/teacher/schedule-change-requests/{id}/propose` | Teacher | 提替代時段 |
| POST | `/student/schedule-change-requests/{id}/withdraw` | Student | 執行前撤回 |

核准 Request：

```json
{
  "expected_request_version": 1,
  "teacher_note": "同意改至週五"
}
```

## 7. 聊天

| Method | Path | 權限 | 說明 |
| --- | --- | --- | --- |
| GET | `/conversations` | Participant | 對話列表與未讀數 |
| GET | `/conversations/{id}/messages` | Participant | 歷史訊息分頁 |
| POST | `/conversations/{id}/messages` | Participant | REST 備援發送 |
| POST | `/conversations/{id}/read` | Participant | 更新已讀位置 |
| WS | `/ws/conversations` | Login | 即時收送與通知 |

發送訊息：

```json
{
  "type": "send_message",
  "conversation_id": "uuid",
  "client_message_id": "uuid",
  "content": "老師您好，我想確認下週上課時間。"
}
```

Server Event：

```json
{
  "type": "message_created",
  "data": {
    "id": "uuid",
    "conversation_id": "uuid",
    "sender_user_id": "uuid",
    "content": "...",
    "created_at": "2026-09-24T10:00:00+08:00"
  }
}
```

## 8. 檔案

| Method | Path | 權限 | 說明 |
| --- | --- | --- | --- |
| POST | `/files/upload-requests` | Login | 申請特定用途上傳 |
| POST | `/files/{id}/complete` | Owner | 回報上傳完成並進入驗證 |
| GET | `/files/{id}` | Authorized | 取得 metadata／受控下載 |
| DELETE | `/files/{id}` | Owner／Admin | 刪除或排程清除 |

`purpose` 必須為後端允許值；每種用途有獨立 MIME、大小與權限限制。

## 9. 教材與測驗

| Method | Path | 權限 | 說明 |
| --- | --- | --- | --- |
| POST | `/teacher/materials` | Teacher | 建立教材紀錄 |
| POST | `/teacher/quizzes/generate` | Teacher | 建立 AI 出題任務 |
| GET | `/teacher/quizzes/{id}` | Teacher | 草稿／狀態 |
| PATCH | `/teacher/quizzes/{id}` | Teacher | 修改標題 |
| PUT | `/teacher/quizzes/{id}/questions/{question_id}` | Teacher | 修改題目與核准答案 |
| POST | `/teacher/quizzes/{id}/publish` | Teacher | 驗證後發布 |
| POST | `/teacher/quizzes/{id}/assignments` | Teacher | 指派學生 |
| GET | `/student/quiz-assignments` | Student | 待完成測驗 |
| POST | `/student/quiz-assignments/{id}/attempts` | Student | 開始作答 |
| POST | `/student/quiz-attempts/{id}/submit` | Student | 提交並自動批改 |
| GET | `/student/quiz-attempts/{id}/result` | Owner | 查看結果 |

## 10. 鋼琴練習

| Method | Path | 權限 | 說明 |
| --- | --- | --- | --- |
| POST | `/teacher/practice-assignments` | Teacher | 建立練習任務 |
| GET | `/student/practice-assignments` | Student | 待完成練習 |
| POST | `/student/practice-assignments/{id}/recordings` | Assigned Student | 建立錄音提交 |
| POST | `/student/practice-recordings/{id}/analyze` | Owner | 建立分析任務 |
| GET | `/practice-recordings/{id}/analysis` | Student Owner／Authorized Teacher | 取得狀態與結果 |

分析回應：

```json
{
  "data": {
    "status": "completed",
    "overall_confidence": 0.74,
    "summary": "整體節奏穩定，後半段可再放慢確認。",
    "segments": [
      {
        "label": "第 4 小節",
        "issue": "tempo_slow",
        "confidence": 0.71,
        "feedback": "這個小節稍微慢了一點，可以搭配節拍器再試一次。"
      }
    ],
    "limitations": ["背景雜音可能影響辨識"]
  },
  "meta": {"request_id": "..."}
}
```

## 11. 主要錯誤碼

| Code | HTTP | 說明 |
| --- | ---: | --- |
| AUTH_REQUIRED | 401 | 未登入或 Session 失效 |
| ROLE_FORBIDDEN | 403 | 角色不允許 |
| TENANT_FORBIDDEN | 403 | 無工作室權限 |
| RESOURCE_NOT_FOUND | 404 | 不存在或刻意隱藏越權資源 |
| INVITATION_INVALID | 400 | 邀請不存在、過期、撤銷或超次數 |
| RELATIONSHIP_REQUIRED | 403 | 無有效師生關係 |
| INVALID_STATE_TRANSITION | 409 | 狀態不可轉換 |
| SCHEDULE_CONFLICT | 409 | 時段或版本衝突 |
| DUPLICATE_MESSAGE | 409 | client_message_id 已存在，可回原訊息 |
| FILE_TYPE_NOT_ALLOWED | 415 | 檔案型別不允許 |
| FILE_SCAN_PENDING | 409 | 尚未通過安全檢查 |
| AI_OUTPUT_INVALID | 502 | AI 輸出未通過 Schema |
| ANALYSIS_LOW_CONFIDENCE | 200 | 非錯誤；結果降級並含限制 |

## 12. Breaking Change 規則

- 不直接移除既有欄位；先新增、遷移、標記 Deprecated，再移除。
- enum 新增可向前相容；重新命名或刪除須 Migration 與 Client 同步。
- API Path、Request 必填欄位或 Response 型別變更須更新 SRS、Frontend 與測試。
- LINE 相關舊 Endpoint 若已存在，先確認無 Client 使用再停用，不直接刪除 Production 資料。

