"""學生找課之後用到的資料表。

課程、接洽對話、綁定碼、課表、課務申請、練習錄音和練習回饋。
每筆資料都記老師與課程，不能只靠學生查詢。
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Course(Base):
    """老師發布的一門鋼琴課。只有已發布可以洽詢。"""

    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_courses_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    delivery_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price_per_lesson: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_slots: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    reference_midi_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class InquiryConversation(Base):
    """一位學生和一門已發布課程的接洽對話。綁定前後是同一段。"""

    __tablename__ = "inquiry_conversations"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_inquiry_conversations_student_course"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ConversationMessage(Base):
    """接洽對話裡的一則訊息。"""

    __tablename__ = "conversation_messages"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "client_message_id",
            name="uq_conversation_messages_client_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inquiry_conversations.id"), nullable=False
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CourseBinding(Base):
    """學生和一門課的上課資格。解除後對話還在，教學功能關閉。"""

    __tablename__ = "course_bindings"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_course_bindings_student_course"),
        CheckConstraint("status IN ('bound', 'unbound')", name="ck_course_bindings_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="bound")
    bound_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    unbound_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BindingCode(Base):
    """只給一位學生、一門課使用的綁定碼。"""

    __tablename__ = "binding_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inquiry_conversations.id"), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class LessonSession(Base):
    """正式課表上的一堂課。老師同意且時段空著之後才會寫入或修改。"""

    __tablename__ = "lesson_sessions"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_lesson_sessions_time_order"),
        CheckConstraint("status IN ('scheduled', 'cancelled')", name="ck_lesson_sessions_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled")


class ChangeRequest(Base):
    """約課、請假或調課。送出後正式課表先不變。"""

    __tablename__ = "change_requests"
    __table_args__ = (
        CheckConstraint("request_type IN ('booking', 'leave', 'reschedule')", name="ck_change_requests_type"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_change_requests_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lesson_sessions.id"), nullable=True)
    request_type: Mapped[str] = mapped_column(String(32), nullable=False)
    proposed_starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    proposed_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PracticeRecording(Base):
    """已綁定學生送出的一次練習錄音。"""

    __tablename__ = "practice_recordings"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_practice_recordings_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PracticeFeedback(Base):
    """一筆練習錄音自己的音高、節奏與文字。失敗時分數保持空白，不顯示 0 分。"""

    __tablename__ = "practice_feedbacks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_practice_feedbacks_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recording_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("practice_recordings.id"), unique=True, nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pitch_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rhythm_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
