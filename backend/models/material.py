from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from backend.models.base import Base

class MaterialDB(Base):
    __tablename__ = "learning_materials"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    teacher_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    filename = Column(
        String(255),
    )

    file_type = Column(
        String(50),
    )

    file_path = Column(
        String(500),
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.now,
    )

