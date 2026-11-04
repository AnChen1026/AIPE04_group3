"""AI 出題的背景工作：老師送出教材與出題設定後在背景出題，完成後老師審查、修改答案，再發成題庫作業。

AI 原本出的題目（questions）和老師審查後實際發出的題目（final_questions）都留著，
之後可以拿來比對 AI 常錯在哪，當成改進提示詞或微調本機模型的資料。
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base

JOB_STATUSES = ("queued", "running", "succeeded", "failed", "published", "discarded")


class QuizGenerationJob(Base):
    __tablename__ = "quiz_generation_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'published', 'discarded')",
            name="ck_quiz_generation_jobs_status",
        ),
        Index("ix_quiz_generation_jobs_teacher", "teacher_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    # 老師在表單填的作業名稱與指派對象，審查完直接用來發作業；沒填的審查時再補
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # {"count": 10, "types": ["single"], "difficulty": "mixed"}
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    # 這次用哪家、哪個模型出的題
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    questions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    final_questions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
