from datetime import datetime, date
from pathlib import Path
from uuid import UUID as UUIDType
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.user import User
from backend.dependencies.common import get_current_user
from backend.models import *
from backend.schemas import *
from backend.dependencies.teacher import get_current_teacher
from backend.services.teacher_sync import _ensure_teacher_profile
from backend.core.uploads import MATERIAL_UPLOAD_DIR

router = APIRouter()

@router.get("/teacher/lessons")
def get_my_lessons(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    return (
        db.query(LessonDB)
        .filter(
            LessonDB.teacher_id == teacher.id
        )
        .all()
    )

@router.get("/teachers/{teacher_id}/lessons")
def get_teacher_lessons(
    teacher_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    if teacher.id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師的課表",
        )

    return (
        db.query(LessonDB)
        .filter(
            LessonDB.teacher_id == teacher.id
        )
        .all()
    )

