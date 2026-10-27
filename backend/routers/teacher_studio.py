"""老師的工作室資料 API。"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.teacher import get_current_teacher
from backend.models.teacher import TeacherDB
from backend.services.student import StudentBusinessError
from backend.services.studio import get_studio, save_studio

router = APIRouter(tags=["工作室"])


class StudioIn(BaseModel):
    name: str
    owner_name: str
    city: str | None = None
    district: str | None = None
    intro: str | None = None


class StudioResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    owner_name: str
    city: str | None
    district: str | None
    intro: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("/teacher/studio", response_model=StudioResponse | None)
def get_my_studio(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """還沒建立就回 null，前端顯示建立表單。"""
    return get_studio(db, teacher.user_id)


@router.put("/teacher/studio", response_model=StudioResponse)
def put_my_studio(
    data: StudioIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """建立或修改自己的工作室。編號第一次建立時由系統產生，之後不會變。"""
    try:
        return save_studio(db, teacher.user_id, data.model_dump())
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
