from datetime import datetime, date
from uuid import UUID as UUIDType
from pydantic import BaseModel

class CourseIn(BaseModel):
    studio_id: UUIDType | None = None

    course_name: str
    course_intros: str

    course_price: int = 0

    class_date: date | None = None

    price_per_lesson: int | None = None

    start_at: datetime
    end_at: datetime

    duration_minutes: int | None = None

    status: str = "draft"

    student_id: UUIDType | None = None

