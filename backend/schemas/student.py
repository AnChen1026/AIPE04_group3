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
    description: str | None = None
    # 沒有上傳圖片時是 null，前端改用預設圖
    image_url: str | None = None

    class Config:
        from_attributes = True


class PublishedCourseResponse(CourseResponse):
    """訪客看得到的已發布課程。不含 MIDI 與圖片的檔案路徑。"""

    teacher_name: str
    teacher_photo_url: str | None = None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    teacher_id: uuid.UUID
    student_id: uuid.UUID
    created_at: datetime
    # 下面是對話列表才有的資訊；剛建立對話時是空的
    course_title: str | None = None
    course_style: str | None = None
    course_level: str | None = None
    teacher_name: str | None = None
    student_name: str | None = None
    bound: bool | None = None
    unread_count: int = 0
    last_message: str | None = None
    last_message_at: datetime | None = None
    # 老師才看得到：已發出、學生還沒使用的綁定碼
    binding_code: str | None = None

    class Config:
        from_attributes = True


class MessageIn(BaseModel):
    body: str
    client_message_id: str | None = None


class BindIn(BaseModel):
    code: str


class ChangeRequestDecision(BaseModel):
    approve: bool


class MessageResponse(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    body: str
    created_at: datetime
    read_at: datetime | None = None
    client_message_id: str | None = None

    class Config:
        from_attributes = True


class LessonResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: str


class TeacherLessonResponse(LessonResponse):
    """老師課表上的一堂課：多了學生與課程名稱。"""

    student_id: uuid.UUID
    student_name: str
    course_title: str

    class Config:
        from_attributes = True


class ChangeRequestResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    request_type: str
    status: str
    created_at: datetime
    session_id: uuid.UUID | None = None
    proposed_starts_at: datetime | None = None
    proposed_ends_at: datetime | None = None
    reason: str | None = None

    class Config:
        from_attributes = True


class TeacherChangeRequestResponse(ChangeRequestResponse):
    """老師看到的課務申請：多了學生、課程與原本那堂課的時間。"""

    student_id: uuid.UUID
    student_name: str
    course_title: str
    session_starts_at: datetime | None = None
    session_ends_at: datetime | None = None


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


class LessonSummaryResponse(BaseModel):
    """課前摘要。只給老師看。"""

    lesson_id: uuid.UUID
    course_id: uuid.UUID
    student_id: uuid.UUID
    lesson_starts_at: datetime
    window_start: datetime | None
    window_end: datetime
    summary_text: str
    written_by: str
    stats: dict
    source_recording_ids: list[str]
    generated_at: datetime
