-- ============================================================
-- 個人工作室智慧管理平台 Data Schema v0.1（MySQL 版）
-- 來源：docs/data_schema_v0.1.md
-- 適用：MySQL 8.0 以上
--
-- 型別對照（文件是 PostgreSQL，這裡改成 MySQL）：
--   uuid        → CHAR(36)
--   varchar     → VARCHAR(長度)
--   text        → TEXT
--   numeric     → DECIMAL
--   integer     → INT
--   date        → DATE
--   timestamptz → DATETIME(6)
-- ============================================================

CREATE DATABASE IF NOT EXISTS aipe04_group3
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE aipe04_group3;

-- ------------------------------------------------------------
-- 2. Account / Studio
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
  id CHAR(36) NOT NULL COMMENT '使用者 ID',
  email VARCHAR(255) NOT NULL COMMENT '登入 Email',
  password_hash VARCHAR(255) NOT NULL COMMENT '密碼雜湊，不可存明碼',
  display_name VARCHAR(100) NOT NULL COMMENT '顯示名稱',
  status VARCHAR(32) NOT NULL COMMENT 'active / suspended / deleted',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '建立時間',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新時間',
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='平台帳號';

CREATE TABLE IF NOT EXISTS studios (
  id CHAR(36) NOT NULL COMMENT '工作室 ID',
  name VARCHAR(100) NOT NULL COMMENT '工作室名稱',
  description TEXT NULL COMMENT '工作室介紹',
  status VARCHAR(32) NOT NULL COMMENT 'active / suspended / closed',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '建立時間',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新時間',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作室基本資料';

CREATE TABLE IF NOT EXISTS studio_members (
  id CHAR(36) NOT NULL COMMENT '關聯 ID',
  studio_id CHAR(36) NOT NULL COMMENT '工作室 ID',
  user_id CHAR(36) NOT NULL COMMENT '使用者 ID',
  role VARCHAR(32) NOT NULL COMMENT 'owner / admin / teacher / assistant',
  status VARCHAR(32) NOT NULL COMMENT 'active / disabled',
  joined_at DATETIME(6) NULL COMMENT '加入時間',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '建立時間',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新時間',
  PRIMARY KEY (id),
  UNIQUE KEY uk_studio_members_studio_user (studio_id, user_id),
  CONSTRAINT fk_studio_members_studio
    FOREIGN KEY (studio_id) REFERENCES studios (id),
  CONSTRAINT fk_studio_members_user
    FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='使用者與工作室的成員關係';

CREATE TABLE IF NOT EXISTS platform_admins (
  id CHAR(36) NOT NULL COMMENT '管理員 ID',
  user_id CHAR(36) NOT NULL COMMENT '平台帳號 ID',
  status VARCHAR(32) NOT NULL COMMENT 'active / disabled',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '建立時間',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新時間',
  PRIMARY KEY (id),
  UNIQUE KEY uk_platform_admins_user (user_id),
  CONSTRAINT fk_platform_admins_user
    FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='平台管理員';

-- ------------------------------------------------------------
-- 3. Course
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS courses (
  id CHAR(36) NOT NULL COMMENT '課程 ID',
  studio_id CHAR(36) NOT NULL COMMENT '工作室 ID',
  teacher_user_id CHAR(36) NOT NULL COMMENT '老師的使用者 ID',
  title VARCHAR(200) NOT NULL COMMENT '課程名稱',
  description TEXT NULL COMMENT '課程介紹',
  price_amount DECIMAL(12,2) NULL COMMENT '課程價格',
  duration_minutes INT NULL COMMENT '單堂分鐘數',
  delivery_mode VARCHAR(32) NULL COMMENT 'onsite / online / hybrid',
  status VARCHAR(32) NOT NULL COMMENT 'draft / active / paused / archived',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '建立時間',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新時間',
  PRIMARY KEY (id),
  CONSTRAINT fk_courses_studio
    FOREIGN KEY (studio_id) REFERENCES studios (id),
  CONSTRAINT fk_courses_teacher
    FOREIGN KEY (teacher_user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='課程資料';

-- ------------------------------------------------------------
-- 4. Student
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS student_profiles (
  id CHAR(36) NOT NULL COMMENT '學生 ID',
  name VARCHAR(100) NOT NULL COMMENT '學生姓名',
  status VARCHAR(32) NOT NULL COMMENT 'active / inactive / deleted',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '建立時間',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新時間',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='學生基本資料';

CREATE TABLE IF NOT EXISTS studio_student_bindings (
  id CHAR(36) NOT NULL COMMENT '綁定 ID',
  studio_id CHAR(36) NOT NULL COMMENT '工作室 ID',
  student_id CHAR(36) NOT NULL COMMENT '學生 ID',
  status VARCHAR(32) NOT NULL COMMENT 'pending / active / revoked',
  bound_at DATETIME(6) NULL COMMENT '綁定時間',
  revoked_at DATETIME(6) NULL COMMENT '解除時間',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '建立時間',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新時間',
  PRIMARY KEY (id),
  UNIQUE KEY uk_bindings_studio_student (studio_id, student_id),
  CONSTRAINT fk_bindings_studio
    FOREIGN KEY (studio_id) REFERENCES studios (id),
  CONSTRAINT fk_bindings_student
    FOREIGN KEY (student_id) REFERENCES student_profiles (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='學生與工作室綁定';

CREATE TABLE IF NOT EXISTS enrollments (
  id CHAR(36) NOT NULL COMMENT '修課關係 ID',
  studio_id CHAR(36) NOT NULL COMMENT '工作室 ID',
  student_id CHAR(36) NOT NULL COMMENT '學生 ID',
  course_id CHAR(36) NOT NULL COMMENT '課程 ID',
  status VARCHAR(32) NOT NULL COMMENT 'active / paused / completed / cancelled',
  started_at DATE NULL COMMENT '開始日期',
  ended_at DATE NULL COMMENT '結束日期',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '建立時間',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新時間',
  PRIMARY KEY (id),
  CONSTRAINT fk_enrollments_studio
    FOREIGN KEY (studio_id) REFERENCES studios (id),
  CONSTRAINT fk_enrollments_student
    FOREIGN KEY (student_id) REFERENCES student_profiles (id),
  CONSTRAINT fk_enrollments_course
    FOREIGN KEY (course_id) REFERENCES courses (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='學生修課關係';

-- ------------------------------------------------------------
-- 5. LINE / Binding
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS line_accounts (
  id CHAR(36) NOT NULL COMMENT 'LINE 帳號 ID',
  student_id CHAR(36) NOT NULL COMMENT '學生 ID',
  line_user_id_hash VARCHAR(255) NOT NULL COMMENT 'LINE User ID Hash',
  line_user_id_ciphertext TEXT NOT NULL COMMENT '加密後 LINE User ID',
  display_name VARCHAR(100) NULL COMMENT 'LINE 顯示名稱',
  status VARCHAR(32) NOT NULL COMMENT 'active / blocked / deleted',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '建立時間',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新時間',
  PRIMARY KEY (id),
  UNIQUE KEY uk_line_accounts_student (student_id),
  UNIQUE KEY uk_line_accounts_hash (line_user_id_hash),
  CONSTRAINT fk_line_accounts_student
    FOREIGN KEY (student_id) REFERENCES student_profiles (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='學生 LINE 身份';

CREATE TABLE IF NOT EXISTS binding_codes (
  id CHAR(36) NOT NULL COMMENT '綁定碼 ID',
  studio_id CHAR(36) NOT NULL COMMENT '工作室 ID',
  code_hash VARCHAR(255) NOT NULL COMMENT '綁定碼 Hash',
  expires_at DATETIME(6) NOT NULL COMMENT '到期時間',
  max_uses INT NOT NULL COMMENT '最大使用次數',
  used_count INT NOT NULL DEFAULT 0 COMMENT '已使用次數',
  status VARCHAR(32) NOT NULL COMMENT 'active / used / expired / revoked',
  created_by CHAR(36) NOT NULL COMMENT '建立者使用者 ID',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '建立時間',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新時間',
  PRIMARY KEY (id),
  UNIQUE KEY uk_binding_codes_hash (code_hash),
  CONSTRAINT fk_binding_codes_studio
    FOREIGN KEY (studio_id) REFERENCES studios (id),
  CONSTRAINT fk_binding_codes_created_by
    FOREIGN KEY (created_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作室綁定碼';

-- ------------------------------------------------------------
-- 6. Message
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS conversations (
  id CHAR(36) NOT NULL COMMENT '對話 ID',
  student_id CHAR(36) NULL COMMENT '學生 ID',
  line_account_id CHAR(36) NULL COMMENT 'LINE 帳號 ID',
  channel VARCHAR(32) NOT NULL COMMENT 'line / web',
  status VARCHAR(32) NOT NULL COMMENT 'active / closed',
  last_message_at DATETIME(6) NULL COMMENT '最後訊息時間',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '建立時間',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新時間',
  PRIMARY KEY (id),
  CONSTRAINT fk_conversations_student
    FOREIGN KEY (student_id) REFERENCES student_profiles (id),
  CONSTRAINT fk_conversations_line_account
    FOREIGN KEY (line_account_id) REFERENCES line_accounts (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='師生或系統對話';

CREATE TABLE IF NOT EXISTS conversation_messages (
  id CHAR(36) NOT NULL COMMENT '訊息 ID',
  conversation_id CHAR(36) NOT NULL COMMENT '對話 ID',
  sender_type VARCHAR(32) NOT NULL COMMENT 'student / teacher / system',
  sender_id CHAR(36) NULL COMMENT '發送者 ID',
  content TEXT NOT NULL COMMENT '訊息內容',
  delivery_status VARCHAR(32) NOT NULL COMMENT 'received / pending / sent / failed',
  external_event_id VARCHAR(255) NULL COMMENT 'LINE Event ID',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '訊息時間',
  PRIMARY KEY (id),
  UNIQUE KEY uk_conversation_messages_event (external_event_id),
  CONSTRAINT fk_conversation_messages_conversation
    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='對話訊息';
