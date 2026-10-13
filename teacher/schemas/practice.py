from datetime import datetime, date
from uuid import UUID as UUIDType
from pydantic import BaseModel

class AssignmentIn(BaseModel):
    course_id: UUIDType

    title: str

    instructions: str | None = None

    reference_file: str | None = None

    due_at: datetime | None = None

