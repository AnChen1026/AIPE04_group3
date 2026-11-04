"""老師發給學生的作業，以及作業附的教材檔案。

作業和課程分開：老師在自己的課程底下，挑一位已綁定的學生發作業。
一份演奏作業可以有自己的參考 MIDI（學生錄音就跟這首比），也可以附多份教材。
檔案本身放在 uploads/assignments/，資料表只記路徑。
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    # performance：演奏作業（錄音繳交、跟參考 MIDI 比）；quiz：題庫作業（AI 從教材出題，題目在 assignment_quiz_questions）
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


class AssignmentQuizQuestion(Base):
    """題庫作業的一題。老師用 AI 從教材出題、預覽後存下來；學生作答時看不到 answers 與 explanation。"""

    __tablename__ = "assignment_quiz_questions"
    __table_args__ = (
        CheckConstraint("question_type IN ('single', 'multiple', 'truefalse')", name="ck_quiz_questions_type"),
        Index("ix_quiz_questions_assignment", "assignment_id", "position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    # single 單選、multiple 多選、truefalse 是非
    question_type: Mapped[str] = mapped_column(String(16), nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String(16), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSONB, nullable=False)
    # 正確選項在 options 裡的位置，單選與是非只有一個
    answers: Mapped[list] = mapped_column(JSONB, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 學生作答時可以看的提示，不能直接講出答案
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)


class QuizAttempt(Base):
    """學生交一次題庫作業。同一份作業可以練很多次，attempt_no 從 1 開始。"""

    __tablename__ = "quiz_attempts"
    __table_args__ = (Index("ix_quiz_attempts_assignment_student", "assignment_id", "student_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    # 答對幾題：畫面不顯示分數，留給之後的分析用
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class QuizAttemptAnswer(Base):
    """一次作答裡的一題：學生選了哪些、對不對。"""

    __tablename__ = "quiz_attempt_answers"
    __table_args__ = (Index("ix_quiz_attempt_answers_attempt", "attempt_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignment_quiz_questions.id", ondelete="CASCADE"), nullable=False
    )
    selected: Mapped[list] = mapped_column(JSONB, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
