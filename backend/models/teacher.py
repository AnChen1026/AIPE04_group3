from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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
        nullable=True,
    )

    seniority = Column(
        Integer,
        nullable=True,
    )

    expertise = Column(
        String(200),
        nullable=True,
    )

    short_intros = Column(
        String(200),
        nullable=True,
    )

    teaching_city = Column(
        String(100),
        nullable=True,
    )

    teaching_district = Column(
        String(100),
        nullable=True,
    )

    target_learning = Column(
        String(255),
        nullable=True,
    )

    teaching_method = Column(
        String(255),
        nullable=True,
    )

    teaching_style = Column(
        String(100),
        nullable=True,
    )

    # 老師照片，沒有上傳時前端用預設圖
    photo_path = Column(
        String(500),
        nullable=True,
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

