from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from backend.models.base import Base

class TeacherDB(Base):
    __tablename__ = "teacher_profiles"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ★ 對應共用 users.id
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    gender = Column(
        String(20),
        nullable=False,
    )

    age = Column(
        Integer,
        nullable=False,
    )

    seniority = Column(
        Integer,
        nullable=False,
    )

    expertise = Column(
        String(200),
        nullable=False,
    )

    short_intros = Column(
        String(200),
        nullable=False,
    )

    teaching_city = Column(
        String(100),
        nullable=False,
    )

    teaching_district = Column(
        String(100),
        nullable=False,
    )

    target_learning = Column(
        String(255),
        nullable=False,
    )

    teaching_method = Column(
        String(255),
        nullable=False,
    )

    teaching_style = Column(
        String(100),
        nullable=False,
    )

    status = Column(
        String(20),
        default="active",
        nullable=False,
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

