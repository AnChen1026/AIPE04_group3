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
    # 有沒有答案與學生的對照樂譜，可以用 score-sheet 網址下載
    has_score_sheet: bool = False

    class Config:
        from_attributes = True


class RecordingResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    # 繳交的是哪一份作業；直接照課程參考曲練習的是空的
    assignment_id: uuid.UUID | None = None
    # 錄音時開的節拍器速度；沒開是空的
    metronome_bpm: float | None = None
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


class AssignmentMaterialResponse(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str | None = None
    file_size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentResponse(BaseModel):
    """一份作業。老師和學生看到的一樣；檔案另外用下載網址拿。"""

    id: uuid.UUID
    course_id: uuid.UUID
    course_title: str
    student_id: uuid.UUID
    student_name: str
    kind: str
    title: str
    description: str | None = None
    due_at: datetime | None = None
    has_midi: bool
    midi_filename: str | None = None
    midi_bpm: float | None = None
    practice_bpm: int | None = None
    materials: list[AssignmentMaterialResponse]
    submission_count: int
    last_submitted_at: datetime | None = None
    created_at: datetime


class AvailabilitySlotIn(BaseModel):
    starts_at: datetime
    ends_at: datetime


class AvailabilitySlotResponse(BaseModel):
    """學生看到的老師可上課時段：只有時間。"""

    id: uuid.UUID
    starts_at: datetime
    ends_at: datetime

    class Config:
        from_attributes = True


class TeacherAvailabilitySlotResponse(AvailabilitySlotResponse):
    """老師自己的時段：多了狀態、預約的學生與課程，以及待處理的約課。"""

    status: str
    student_id: uuid.UUID | None = None
    student_name: str | None = None
    course_id: uuid.UUID | None = None
    course_title: str | None = None
    lesson_id: uuid.UUID | None = None
    change_request_id: uuid.UUID | None = None


class SlotBookingIn(BaseModel):
    """學生在開放時段內選開始時間與長度。"""

    starts_at: datetime | None = None
    minutes: int | None = None
    reason: str | None = None


class SlotRescheduleIn(BaseModel):
    """學生把一堂課調到開放時段內，長度沿用原本那堂。"""

    session_id: uuid.UUID
    starts_at: datetime
    reason: str | None = None


class WeeklyWindow(BaseModel):
    """每週的一段時間。weekday 0 是週一；分鐘是當天的第幾分鐘，例如 18:00 是 1080。"""

    weekday: int
    start_minute: int
    end_minute: int

    class Config:
        from_attributes = True


class WeeklyAvailabilityIn(BaseModel):
    windows: list[WeeklyWindow]


class RecurringLessonIn(WeeklyWindow):
    student_id: uuid.UUID
    course_id: uuid.UUID


class RecurringLessonUpdateIn(WeeklyWindow):
    """move_lesson_ids：老師勾選要一起移到新時間的課，其他已排的課保留。"""

    move_lesson_ids: list[uuid.UUID] = []


class RecurringLessonStopIn(BaseModel):
    """cancel_lesson_ids：老師勾選要一起取消的課，其他已排的課保留。"""

    cancel_lesson_ids: list[uuid.UUID] = []


class RecurringFutureLesson(BaseModel):
    id: uuid.UUID
    starts_at: datetime
    ends_at: datetime

    class Config:
        from_attributes = True


class RecurringLessonResponse(WeeklyWindow):
    id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    course_id: uuid.UUID
    course_title: str
    future_lessons: list[RecurringFutureLesson]


class RecurringSkippedWeek(BaseModel):
    starts_at: datetime
    ends_at: datetime
    reason: str


class RecurringLessonResult(BaseModel):
    """created：排了或移動了幾堂；skipped：因衝突沒排成的那幾週。"""

    rule: RecurringLessonResponse
    created: int
    skipped: list[RecurringSkippedWeek]


class TeacherLessonIn(BaseModel):
    """老師直接排課。課的時間由老師決定；slot_id 是放在哪個開放時段上，時段會讓出這段時間。"""

    student_id: uuid.UUID
    course_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    slot_id: uuid.UUID | None = None
