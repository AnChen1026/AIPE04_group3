from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from backend.models.base import Base

class AssignmentDB(Base):
    __tablename__ = "practice_assignments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id"),
        nullable=False,
    )

    teacher_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teacher_profiles.id"),
        nullable=False,
    )

    title = Column(
        String(200),
        nullable=False,
    )

    instructions = Column(Text)

    reference_file = Column(
        String(255),
    )

    status = Column(
        String(20),
        default="draft",
    )

    due_at = Column(
        DateTime,
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

class SubmissionDB(Base):
    __tablename__ = "practice_submissions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("practice_assignments.id"),
        nullable=False,
    )

    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    audio_file = Column(
        String(255),
    )

    # pending / processing / completed / failed
    processing_status = Column(
        String(20),
        default="pending",
    )

    submitted_at = Column(
        DateTime,
        default=datetime.now,
    )

class EvaluationDB(Base):
    __tablename__ = "practice_evaluations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    submission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("practice_submissions.id"),
        nullable=False,
    )

    score = Column(
        Float,
    )

    analysis = Column(Text)

    recommendation = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

