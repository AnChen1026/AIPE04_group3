from datetime import datetime, date
from pathlib import Path
from uuid import UUID as UUIDType
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.user import User
from backend.dependencies import get_current_user
from teacher.models import *
from teacher.schemas import *
from teacher.dependencies.teacher import get_current_teacher
from teacher.services.teacher_sync import _ensure_teacher_profile
from teacher.core.uploads import MATERIAL_UPLOAD_DIR

router = APIRouter()

@router.get("/teacher/quizzes")
def get_my_quizzes(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    return (
        db.query(QuizDB)
        .filter(
            QuizDB.teacher_id == teacher.id
        )
        .all()
    )

@router.get("/teachers/{teacher_id}/quizzes")
def get_teacher_quizzes(
    teacher_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    if teacher.id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師的測驗",
        )

    return (
        db.query(QuizDB)
        .filter(
            QuizDB.teacher_id == teacher.id
        )
        .all()
    )

