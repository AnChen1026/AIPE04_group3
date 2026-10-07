import uuid
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

# --- 洽詢相關 ---
class InquiryCreate(BaseModel):
    course_id: uuid.UUID
    inquiry_text: str = Field(..., max_length=1000)
    client_request_id: uuid.UUID

class InquiryResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    student_id: uuid.UUID
    message: str
    reply_text: Optional[str] = None
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- 課表與課務相關 ---
class LessonSessionResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    starts_at: datetime  # 對齊 命名
    ends_at: datetime    # 對齊 命名
    location: Optional[str] = None
    status: str
    class Config:
        from_attributes = True

class ChangeRequestCreate(BaseModel):
    session_id: uuid.UUID # 對齊 命名
    request_type: str = Field(..., description="booking, leave, reschedule")
    reason: Optional[str] = None
    client_request_id: uuid.UUID

# --- 錄音作業提交相關 ---
class SubmissionAsyncResponse(BaseModel):
    submission_id: uuid.UUID
    assignment_id: uuid.UUID
    status: str
    message: str
