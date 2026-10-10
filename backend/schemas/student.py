from pydantic import BaseModel, Field
import uuid
from typing import Optional, List
from datetime import datetime, date

# --- 學生個人資料 ---
class StudentProfileSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    current_level: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True

class StudentProfileUpdate(BaseModel):
    current_level: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=500)

# --- 課程洽詢 ---
class InquiryCreate(BaseModel):
    course_id: uuid.UUID
    message: str = Field(..., max_length=1000, description="洽詢訊息內容")
    client_request_id: uuid.UUID
    recommendation_session_id: Optional[uuid.UUID] = None

class InquiryResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    student_id: uuid.UUID
    message: str
    teacher_response: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- 修課紀錄 ---
class EnrollmentResponse(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    course_id: uuid.UUID
    status: str
    started_at: Optional[date] = None
    ended_at: Optional[date] = None

    class Config:
        from_attributes = True



class LessonSessionResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    location: Optional[str] = None
    status: str
    version: int
    class Config:
        from_attributes = True

class ChangeRequestCreate(BaseModel):
    enrollment_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None # 約新課可不填；請假調課必填
    request_type: Literal["booking", "leave", "reschedule"]
    proposed_payload: dict = Field(default_factory=dict, description="期望變更的時間(格式如:{'starts_at': '...', 'ends_at': '...'})")
    reason: Optional[str] = Field(None, max_length=500)
    client_request_id: uuid.UUID

class ChangeRequestResponse(BaseModel):
    id: uuid.UUID
    enrollment_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    request_type: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True



class AssignmentResponse(BaseModel):
    id: uuid.UUID
    enrollment_id: uuid.UUID
    title: str
    instructions: Optional[str] = None
    due_at: Optional[datetime] = None
    status: str
    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    audio_file_id: uuid.UUID # 經由 FILE-01 端點驗證上傳後拿到的 ready 檔案 ID
    duration_seconds: float = Field(..., gt=0, description="錄音時長必須大於零秒")
    client_submission_id: uuid.UUID

class EvaluationResponse(BaseModel):
    pitch_score: Optional[float] = None
    rhythm_score: Optional[float] = None
    total_score: Optional[float] = None
    feedback_text: Optional[str] = None
    feedback_status: str

class SubmissionHistoryResponse(BaseModel):
    id: uuid.UUID
    audio_file_id: uuid.UUID
    duration_seconds: float
    processing_status: str
    failure_code: Optional[str] = None
    submitted_at: datetime
    evaluation: Optional[EvaluationResponse] = None
    class Config:
        from_attributes = True
