from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from backend.models.base import Base

class ConversationDB(Base):
    __tablename__ = "conversations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

class MessageDB(Base):
    __tablename__ = "messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False,
    )

    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    receiver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    content = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

