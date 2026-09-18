# 個人工作室智慧管理平台 Data Schema

| 項目 | 內容 |
|---|---|
| 版本 | v0.1 |
| 階段 | 第一週開發版本 |
| 資料庫 | PostgreSQL |
| 範圍 | 註冊登入、工作室、課程、學生、LINE 訊息、平台管理員 |

---

## 1. 設計原則

- 使用 `studio_id` 作為工作室資料隔離依據。
- 主鍵建議使用 UUID。
- 主要資料表建議保留 `created_at`、`updated_at`。
- 密碼只保存 Hash，不保存明碼。
- LINE User ID 應避免直接明文保存。
- 第一版暫不建立 AI 推薦、課表異動、堂數與收款相關資料表。

---

# 2. Account / Studio

## 2.1 `users`

平台帳號。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 使用者 ID |
| email | varchar UNIQUE | 登入 Email |
| password_hash | varchar | 密碼雜湊 |
| display_name | varchar | 顯示名稱 |
| status | varchar | active / suspended / deleted |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

---

## 2.2 `studios`

工作室基本資料。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 工作室 ID |
| name | varchar | 工作室名稱 |
| description | text nullable | 工作室介紹 |
| status | varchar | active / suspended / closed |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

---

## 2.3 `studio_members`

記錄使用者屬於哪個工作室，以及在工作室中的角色。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 關聯 ID |
| studio_id | uuid FK | → studios.id |
| user_id | uuid FK | → users.id |
| role | varchar | owner / admin / teacher / assistant |
| status | varchar | active / disabled |
| joined_at | timestamptz nullable | 加入時間 |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

**限制：** `UNIQUE(studio_id, user_id)`

---

## 2.4 `platform_admins`

記錄哪些平台帳號具有平台管理員權限。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 管理員 ID |
| user_id | uuid FK UNIQUE | → users.id |
| status | varchar | active / disabled |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

---

# 3. Course

## 3.1 `courses`

工作室建立與管理的課程資料。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 課程 ID |
| studio_id | uuid FK | → studios.id |
| teacher_user_id | uuid FK | → users.id |
| title | varchar | 課程名稱 |
| description | text nullable | 課程介紹 |
| price_amount | numeric(12,2) nullable | 課程價格 |
| duration_minutes | integer nullable | 單堂分鐘數 |
| delivery_mode | varchar nullable | onsite / online / hybrid |
| status | varchar | draft / active / paused / archived |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

---

# 4. Student

## 4.1 `student_profiles`

學生基本資料。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 學生 ID |
| name | varchar | 學生姓名 |
| status | varchar | active / inactive / deleted |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

---

## 4.2 `studio_student_bindings`

記錄學生與工作室的關係，同一學生可綁定多個工作室。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 綁定 ID |
| studio_id | uuid FK | → studios.id |
| student_id | uuid FK | → student_profiles.id |
| status | varchar | pending / active / revoked |
| bound_at | timestamptz nullable | 綁定時間 |
| revoked_at | timestamptz nullable | 解除時間 |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

**限制：** `UNIQUE(studio_id, student_id)`

---

## 4.3 `enrollments`

記錄學生目前正在修讀哪些課程。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 修課關係 ID |
| studio_id | uuid FK | → studios.id |
| student_id | uuid FK | → student_profiles.id |
| course_id | uuid FK | → courses.id |
| status | varchar | active / paused / completed / cancelled |
| started_at | date nullable | 開始日期 |
| ended_at | date nullable | 結束日期 |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

---

# 5. LINE / Binding

## 5.1 `line_accounts`

保存學生的 LINE 身份，供系統辨識 LINE 使用者。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | LINE 帳號 ID |
| student_id | uuid FK UNIQUE | → student_profiles.id |
| line_user_id_hash | varchar UNIQUE | LINE User ID Hash |
| line_user_id_ciphertext | text | 加密後 LINE User ID |
| display_name | varchar nullable | LINE 顯示名稱 |
| status | varchar | active / blocked / deleted |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

---

## 5.2 `binding_codes`

老師產生給學生使用的工作室綁定碼。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 綁定碼 ID |
| studio_id | uuid FK | → studios.id |
| code_hash | varchar UNIQUE | 綁定碼 Hash |
| expires_at | timestamptz | 到期時間 |
| max_uses | integer | 最大使用次數 |
| used_count | integer | 已使用次數 |
| status | varchar | active / used / expired / revoked |
| created_by | uuid FK | → users.id |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

---

# 6. Message

## 6.1 `conversations`

代表一段學生與平台、AI 或老師之間的對話。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 對話 ID |
| student_id | uuid FK nullable | → student_profiles.id |
| line_account_id | uuid FK nullable | → line_accounts.id |
| channel | varchar | line / web |
| status | varchar | active / closed |
| last_message_at | timestamptz nullable | 最後訊息時間 |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

---

## 6.2 `conversation_messages`

保存每一則學生、老師或系統訊息。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 訊息 ID |
| conversation_id | uuid FK | → conversations.id |
| sender_type | varchar | student / teacher / system |
| sender_id | uuid nullable | 發送者 ID |
| content | text | 訊息內容 |
| delivery_status | varchar | received / pending / sent / failed |
| external_event_id | varchar nullable UNIQUE | LINE Event ID |
| created_at | timestamptz | 訊息時間 |

---

# 7. 第一版關聯摘要

```text
users
 └── studio_members ─── studios
                         └── courses

student_profiles
 ├── studio_student_bindings ─── studios
 ├── enrollments ─── courses
 └── line_accounts
        └── conversations
              └── conversation_messages

studios
 └── binding_codes

users
 └── platform_admins
```

---

# 8. 第一版暫不建立

以下功能尚未進入第一週開發範圍，因此暫不建立相關資料表：

- AI 課程推薦
- 課程程度 L1～L4
- 課程推薦紀錄
- 課表與實際課堂
- 請假／調課異動
- 多方同意流程
- 堂數管理
- 收款紀錄
- AI 人工接管路由
- 訂閱與外部推廣
