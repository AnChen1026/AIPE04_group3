from datetime import datetime, date
from uuid import UUID as UUIDType
from pydantic import BaseModel

class BindingIn(BaseModel):
    studio_id: UUIDType
    student_id: UUIDType

