from datetime import datetime, date
from uuid import UUID as UUIDType
from pydantic import BaseModel

class MessageIn(BaseModel):
    conversation_id: UUIDType
    receiver_id: UUIDType
    content: str

