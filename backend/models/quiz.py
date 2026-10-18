from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from backend.models.base import Base

class QuizDB(Base):
    __tablename__ = "quizzes"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    teacher_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teacher_profiles.id"),
        nullable=False,
    )

    title = Column(
        String(200),
    )

    question = Column(
        Text,
    )

    answer = Column(
        Text,
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

