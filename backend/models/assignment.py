"""老師發給學生的作業，以及作業附的教材檔案。

作業和課程分開：老師在自己的課程底下，挑一位已綁定的學生發作業。
一份演奏作業可以有自己的參考 MIDI（學生錄音就跟這首比），也可以附多份教材。
檔案本身放在 uploads/assignments/，資料表只記路徑。
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Assignment(Base):
    """一份作業：哪位老師、哪門課、給哪位學生、內容與繳交期限。"""

    __tablename__ = "assignments"
    __table_args__ = (
        CheckConstraint("kind IN ('performance', 'quiz')", name="ck_assignments_kind"),
        Index("ix_assignments_teacher", "teacher_id"),
        Index("ix_assignments_student_course", "student_id", "course_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # performance：演奏作業（錄音繳交、跟參考 MIDI 比）；quiz：題庫作業（作答由 AI 測驗負責，這裡只放教材）
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="performance")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    midi_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    midi_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 參考 MIDI 本身的速度；學生的節拍器沒有老師指定時，預設用這個
    midi_bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 老師指定的練習速度（可以比原曲慢），學生開節拍器時預設用這個
    practice_bpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AssignmentMaterial(Base):
    """作業附的一份教材：樂譜、講義、老師錄的示範音檔等。"""

    __tablename__ = "assignment_materials"
    __table_args__ = (Index("ix_assignment_materials_assignment", "assignment_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
