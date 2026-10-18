from pydantic import BaseModel


class CourseIn(BaseModel):
    title: str
    level: str | None = None
    style: str | None = None
    delivery_mode: str | None = None
    region: str | None = None
    price_per_lesson: int | None = None
    time_slots: str | None = None
    status: str = "draft"


class CourseUpdate(BaseModel):
    """只改有傳的欄位。要清空某欄就傳 null 或空字串。"""

    title: str | None = None
    level: str | None = None
    style: str | None = None
    delivery_mode: str | None = None
    region: str | None = None
    price_per_lesson: int | None = None
    time_slots: str | None = None
    status: str | None = None
