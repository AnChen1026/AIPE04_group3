from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from backend.models.base import Base

class CourseDB(Base):
    # 學生端已經用 courses 這張表，老師端改用自己的表名，兩邊才能同時掛在 app.py。
    __tablename__ = "teacher_module_courses"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    studio_id = Column(
        UUID(as_uuid=True),
        ForeignKey("studios.id"),
    )

    teacher_profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teacher_profiles.id"),
        nullable=False,
    )

    course_name = Column(
        String(200),
        nullable=False,
    )

    course_intros = Column(
        String(200),
        nullable=False,
    )

    course_price = Column(
        Integer,
        nullable=False,
        default=0,
    )

    class_date = Column(
        Date,
        nullable=True,
    )

    price_per_lesson = Column(
        Integer,
    )

    start_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    end_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    duration_minutes = Column(
        Integer,
    )

    status = Column(
        String(20),
        default="draft",
        nullable=False,
    )

    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )

class InquiryDB(Base):
    __tablename__ = "course_inquiries"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teacher_module_courses.id"),
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
        ForeignKey("teacher_module_courses.id"),
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

