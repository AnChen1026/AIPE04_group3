from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from backend.models.base import Base

class StudioDB(Base):
    __tablename__ = "studios"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    studio_owner = Column(
        String(100),
        nullable=False,
    )

    description = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )

class BindingDB(Base):
    __tablename__ = "studio_student_bindings"

    __table_args__ = (
        UniqueConstraint(
            "studio_id",
            "teacher_id",
            "student_id",
            name="uq_studio_teacher_student",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    studio_id = Column(
        UUID(as_uuid=True),
        ForeignKey("studios.id"),
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

    requested_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # pending / active / rejected / inactive
    status = Column(
        String(20),
        default="pending",
        nullable=False,
    )

    teacher_confirmed_at = Column(
        DateTime,
    )

    student_confirmed_at = Column(
        DateTime,
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

