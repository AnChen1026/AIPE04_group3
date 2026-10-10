import uuid
from datetime import datetime, date
from sqlalchemy import String, ForeignKey, DateTime, func, CheckConstraint, Boolean, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base

class StudentProfile(Base):
    """學生擴充資料表 """
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 連回 users.id，當 user 被刪除時使用 RESTRICT 保護學生學習歷史不被輕易連帶刪除
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), unique=True, nullable=False)
    
    # 程度與備註（保留給前端或推薦系統微調使用）
    current_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # ORM 關係對照
    user = relationship("User", back_populates="student_profile")
    enrollments = relationship("Enrollment", back_populates="student")
    course_inquiries = relationship("CourseInquiry", back_populates="student")


class CourseInquiry(Base):
    """站內課程洽詢資料表"""
    __tablename__ = "course_inquiries"
    __table_args__ = (
        CheckConstraint("status IN ('new', 'responded', 'closed', 'cancelled')", name="ck_course_inquiries_status"),
        UniqueConstraint("student_id", "client_request_id", name="uq_course_inquiries_student_client_request"),
    )


    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=False) 
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    recommendation_session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    message: Mapped[str] = mapped_column(String(1000), nullable=False) 
    teacher_response: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    
    # 提交去重鍵，防止前端連點造成重複發起洽詢
    client_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    student = relationship("StudentProfile", back_populates="course_inquiries")


class Enrollment(Base):
    """正式修課紀錄表"""
    __tablename__ = "enrollments"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'completed', 'cancelled')", name="ck_enrollments_status"),
        UniqueConstraint("course_id", "student_id", name="uq_enrollments_course_student"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False) # 租戶邊界
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    started_at: Mapped[date | None] = mapped_column(nullable=True)
    ended_at: Mapped[date | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    student = relationship("StudentProfile", back_populates="enrollments")


# ======================================================================
# 排課、課堂參與、與課務異動申請相關

class LessonSession(Base):
    """單次課堂（老師與學生個人課表主檔）"""
    __tablename__ = "lesson_sessions"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_lesson_sessions_time_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False) # 租戶隔離
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    teacher_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False) # 授課老師
    
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled") # scheduled, completed, cancelled
    version: Mapped[integer] = mapped_column(Integer, default=1, server_default="1") # 樂觀鎖版本檢查

    participants = relationship("SessionParticipant", back_populates="session")


class SessionParticipant(Base):
    """課堂學生參與狀態表（請假、出席紀錄）"""
    __tablename__ = "session_participants"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_participants_session_student"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lesson_sessions.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=False)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=False)
    
    attendance_status: Mapped[str] = mapped_column(String(32), nullable=False, default="expected") # expected, present, absent, leave, cancelled

    session = relationship("LessonSession", back_populates="participants")


class ChangeRequest(Base):
    """約課／請假／調課異動申請表"""
    __tablename__ = "change_requests"
    __table_args__ = (
        CheckConstraint("request_type IN ('booking', 'leave', 'reschedule')", name="ck_change_requests_type"),
        CheckConstraint("status IN ('pending', 'approved', 'executed', 'rejected', 'cancelled', 'expired', 'conflict')", name="ck_change_requests_status"),
        UniqueConstraint("requester_user_id", "client_request_id", name="uq_change_requests_user_client_request"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lesson_sessions.id"), nullable=True) # 新約課可為空
    
    requester_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False) # 申請發起人
    request_type: Mapped[str] = mapped_column(String(32), nullable=False) # booking, leave, reschedule
    
    # 存放變更前後的快照與希望變更的內容
    before_payload: Mapped[dict | None] = mapped_column(func.jsonb(), nullable=True)
    proposed_payload: Mapped[dict | None] = mapped_column(func.jsonb(), nullable=True) # 存放欲調整的時間、地點等
    
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    
    expected_session_version: Mapped[integer | None] = mapped_column(Integer, nullable=True) # 樂觀鎖版本防衝突
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 提交去重鍵，防止前端連點
    client_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)


class ChangeRequestApproval(Base):
    """異動審核紀錄表"""
    __tablename__ = "change_request_approvals"
    __table_args__ = (
        UniqueConstraint("change_request_id", "required_role", name="uq_change_request_approvals_request_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    change_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("change_requests.id"), nullable=False)
    approver_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    required_role: Mapped[str] = mapped_column(String(32), nullable=False) # student, teacher
    decision: Mapped[str] = mapped_column(String(32), nullable=False, default="pending") # pending, approved, rejected
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)




# ====================================================================
# 練習作業（Practice Assignments）與錄音提交評分相關 


class PracticeAssignment(Base):
    """老師發布的指定學生 MIDI 練習作業"""
    __tablename__ = "practice_assignments"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_practice_assignments_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=False)
    created_by_teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False) # 出題老師 Profile ID
    reference_file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False) # 經校驗的參考 MIDI 檔案識別碼
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_metadata: Mapped[dict | None] = mapped_column(func.jsonb(), nullable=True) # 存放拍號、速度、小節起算位置等 JSON 快照
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft") # draft, published, archived

    submissions = relationship("PracticeSubmission", back_populates="assignment")


class PracticeSubmission(Base):
    """學生麥克風錄音提交歷史（一次作業可多次提交，每次皆保存）"""
    __tablename__ = "practice_submissions"
    __table_args__ = (
        CheckConstraint("processing_status IN ('pending', 'processing', 'completed', 'failed')", name="ck_practice_submissions_status"),
        UniqueConstraint("student_id", "client_submission_id", name="uq_practice_submissions_student_client_submission"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("practice_assignments.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=False)
    audio_file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False) # 指向私有儲存 ready 的錄音檔 metadata ID
    
    duration_seconds: Mapped[float] = mapped_column(DateTime(timezone=False), nullable=False) # 錄音時長（秒）
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending") # pending, processing, completed, failed
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True) # 慢速任務分析失敗的原因代碼
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # 提交去重鍵，防止麥克風上傳因連點產生重複辨識任務
    client_submission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    assignment = relationship("PracticeAssignment", back_populates="submissions")
    evaluation = relationship("PracticeEvaluation", back_populates="submission", uselist=False)


class PracticeEvaluation(Base):
    """結構化評分與 LLM 自然語言回饋（分析失敗不顯示 0 分，保留結構化分析）"""
    __tablename__ = "practice_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("practice_submissions.id"), unique=True, nullable=False)
    
    # 分數在尚未算出或分析失敗（failed）時保持為 NULL，前端絕不盲目顯示 0 分
    pitch_score: Mapped[float | None] = mapped_column(nullable=True) # 音高分
    rhythm_score: Mapped[float | None] = mapped_column(nullable=True) # 節奏分
    total_score: Mapped[float | None] = mapped_column(nullable=True) # 綜合總分
    
    extracted_events: Mapped[dict | None] = mapped_column(func.jsonb(), nullable=True) # 辨識出的音高、onset、duration JSON
    comparison_result: Mapped[dict | None] = mapped_column(func.jsonb(), nullable=True) # 小節拍位置、漏音多彈等判定 JSON
    scoring_config: Mapped[dict | None] = mapped_column(func.jsonb(), nullable=True) # 本次評分容許誤差與權重快照
    analysis_version: Mapped[str | None] = mapped_column(String(64), nullable=True) # 分析模組版本
    
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True) # LLM 文字回饋
    feedback_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending") # pending, completed, failed
    llm_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    submission = relationship("PracticeSubmission", back_populates="evaluation")

