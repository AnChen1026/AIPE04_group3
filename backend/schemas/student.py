"""學生 API 回傳的資料形狀。"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class CourseResponse(BaseModel):
    id: uuid.UUID
    teacher_id: uuid.UUID
    title: str
    level: str | None = None
    style: str | None = None
    delivery_mode: str | None = None
    region: str | None = None
    price_per_lesson: int | None = None
    time_slots: str | None = None
    status: str
    has_reference_midi: bool = False

    class Config:
        from_attributes = True


class PublishedCourseResponse(CourseResponse):
    """訪客看得到的已發布課程。不含 MIDI 路徑。"""

    teacher_name: str


class ConversationResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    teacher_id: uuid.UUID
    student_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


class LessonResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: str

    class Config:
        from_attributes = True


class ChangeRequestResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    request_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackResponse(BaseModel):
    pitch_score: float | None = None
    rhythm_score: float | None = None
    feedback_text: str | None = None
    status: str

    class Config:
        from_attributes = True


class RecordingResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    status: str
    submitted_at: datetime
    feedback: FeedbackResponse | None = None

    class Config:
        from_attributes = True


class TeacherRecordingResponse(RecordingResponse):
    """老師看到的一筆練習：多了是哪位學生。"""

    student_id: uuid.UUID
    student_name: str
