from datetime import datetime
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from backend.models.base import Base

class InquiryDB(Base):
    __tablename__ = "course_inquiries"

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

    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    message = Column(Text)

    reply = Column(Text)

    status = Column(
        String(20),
        default="pending",
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

    replied_at = Column(
        DateTime,
    )

class LessonDB(Base):
    __tablename__ = "teacher_lesson_sessions"

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

    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    start_time = Column(
        DateTime,
    )

    end_time = Column(
        DateTime,
    )

    status = Column(
        String(20),
        default="scheduled",
    )

    notes = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

class ChangeRequestDB(Base):
    __tablename__ = "teacher_change_requests"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    lesson_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teacher_lesson_sessions.id"),
        nullable=False,
    )

    requester_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    request_type = Column(
        String(50),
    )

    reason = Column(Text)

    new_start_time = Column(
        DateTime,
    )

    new_end_time = Column(
        DateTime,
    )

    status = Column(
        String(20),
        default="pending",
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

